import csv
import json
import zipfile
import requests
import fitz
import pandas as pd
import re

last_name = 'Pelosi'
first_name = 'Nancy'
years = [2019, 2020, 2021]

def parse_disclosure_doc(doc):
    """
    Parse the disclosure doc and extract all the option trading records.
    """
    n = len(doc)

    # A doc might contain multiple pages. Combine their contents together.
    blocks = []
    for i in range(n):
        page = doc.load_page(page_id=i)
        json_data = page.get_text('json')
        json_data = json.loads(json_data)
        blocks.extend(json_data['blocks'])

    transactions = []
    transaction = {}
    for block in blocks:
        sp_found = False
        date_found = False
        symbol_found = False
        descr_found = False
        if 'lines' in block and block['lines']:
            for line in block['lines']:
                if 'spans' in line:
                    for span in line['spans']:
                        if "text" in span:
                            words = span['text'].split()
                            if len(words) == 0: continue
                            # Based on what we have observed so far, we assume that
                            # if a word contains two '/', then it denotes a date and
                            # the first occurrence of a date is the transaction date.
                            if words[0].count('/') == 2 and not date_found:
                                date_found = True
                                transaction['transaction_date'] = words[0]
                            # We found that the symbol always comes after 'SP'
                            elif words[-1].upper() == 'SP':
                                sp_found = True
                            elif sp_found:
                                p = re.compile(".*\((.*)\).*")
                                try:
                                    transaction['symbol'] = p.search(span['text']).group(1).upper()
                                    sp_found = False
                                except:
                                    pass
                            # The description comes after the string 'ESCRIPTION'
                            elif span['text'].upper() == 'ESCRIPTION':
                                descr_found = True
                            elif descr_found:
                                descr_found = False
                                for w in words:
                                    if '$' in w:
                                        transaction['strike'] = float(w[1:].replace(',',''))
                                    elif '/' in w:
                                        if w[-1] == '.':
                                            transaction['expiration'] = w[:-1]
                                        else:
                                            transaction['expiration'] = w
                                    elif w.lower() in ('call','put'):
                                        transaction['contract_type'] = w.lower()
                                    elif w.lower() in ("exercised", "purchased", "sold"):
                                        transaction['action'] = w.lower()
                                    elif w.isnumeric():
                                        transaction['quantity'] = float(w)
                                if len(transaction) == 7:
                                    transactions.append(transaction.copy())
                                transaction.clear()
    return transactions

def main():
    transactions = []
    for year in years:
        print("Fetching the doc for the year of {} ...".format(year))
        disclosure_zip_file = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{}FD.ZIP'.format(year)
        disclosure_pdf_file = 'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{}/'.format(year)
        r = requests.get(disclosure_zip_file)
        zipfile_name = '{}.zip'.format(year)

        with open(zipfile_name, 'wb') as f:
            f.write(r.content)

        with zipfile.ZipFile(zipfile_name) as z:
            z.extractall('.')

        df = pd.read_csv('{}FD.txt'.format(year), sep= "\t")
        df = df[(df['Last'] == last_name) &
                (df['First'] == first_name) &
                (df['FilingType'] == 'P')]

        if df.empty:
            print("There are no records for the person in the year of {}".format(year))
            continue

        cur = []
        for doc_id in df['DocID']:
            r = requests.get(f"{disclosure_pdf_file}{doc_id}.pdf")
            with open(f"{doc_id}.pdf", 'wb') as pdf_file:
                pdf_file.write(r.content)
            disclosure_doc = fitz.open('{}.pdf'.format(doc_id))
            try:
                cur.extend(parse_disclosure_doc(disclosure_doc))
            except:
                pass
        if cur:
            cur = pd.DataFrame(data=cur)
            cur['year_of_doc'] = year
            transactions.append(cur)
        else:
            print("There are no option trading records for the person in the year of {}".format(year))

    if transactions:
        transactions = pd.concat(transactions)
        transactions.to_csv("pelosi_option_trading.csv")


if __name__ == "__main__":
    main()
import csv
import json
import zipfile
import requests
import fitz
import pandas as pd
import re

last_name = 'Pelosi'
first_name = 'Nancy'
years = [2020, 2021]

def parse_disclosure_doc(doc):
    n = len(doc)
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
        symbol_found = False
        descr_found = False
        if 'lines' in block and block['lines']:
            for line in block['lines']:
                if 'spans' in line:
                    for span in line['spans']:
                        if "text" in span and len(span['text'].split()):
                            if span['text'].split()[-1].upper() == 'SP':
                                sp_found = True
                            elif sp_found:
                                p = re.compile(".*\((.*)\).*")
                                try:
                                    transaction['symbol'] = p.search(line['spans'][0]['text']).group(1).upper()
                                    sp_found = False
                                except:
                                    pass
                            elif span['text'].upper() == 'ESCRIPTION':
                                descr_found = True
                            elif descr_found:
                                descr_found = False
                                descr = span['text'].split()
                                for w in descr:
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
                                if len(transaction) ==  6:
                                    transactions.append(transaction.copy())
                                transaction.clear()
    return transactions

def main():
    transactions = []
    for year in years:
        print(year)
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

        cur = []
        for doc_id in df['DocID']:
            print(doc_id)
            r = requests.get(f"{disclosure_pdf_file}{doc_id}.pdf")
            with open(f"{doc_id}.pdf", 'wb') as pdf_file:
                pdf_file.write(r.content)
            disclosure_doc = fitz.open('{}.pdf'.format(doc_id))
            try:
                cur.extend(parse_disclosure_doc(disclosure_doc))
            except:
                pass

        cur = pd.DataFrame(data=cur)
        cur['year_of_doc'] = year
        transactions.append(cur)

    transactions = pd.concat(transactions)
    transactions.to_csv("pelosi_option_trading.csv")


if __name__ == "__main__":
    main()
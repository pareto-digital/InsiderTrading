import csv
import json
import zipfile
import requests
import fitz

year = 2016
Investor_Last_Name = 'Pelosi'

# File download
while year <= 2022:
    disclosure_zip_file = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{}FD.ZIP'.format(year)
    disclosure_pdf_file = 'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{}/'.format(year)

    r = requests.get(disclosure_zip_file)
    zipfile_name = '{}.zip'.format(year)

    with open(zipfile_name, 'wb') as f:
        f.write(r.content)

    # Unzip
    with zipfile.ZipFile(zipfile_name) as z:
        z.extractall('.')

    with open('{}FD.txt'.format(year)) as fd:
        for line in csv.reader(fd, delimiter='\t'):
            # print(line)
            if (line[1] == Investor_Last_Name) & (line[4] == 'P'):  # Define filing type P as public
                print('{}FD.txt'.format(year), line)
                doc_id = line[8]
                date = line[7]
                r = requests.get(f"{disclosure_pdf_file}{doc_id}.pdf")

                with open(f"{doc_id}.pdf", 'wb') as pdf_file:
                    pdf_file.write(r.content)
    year += 1


# File read
year = 2020
while year < 2021:
    print(year)
    with open('{}FD.txt'.format(year)) as fd:
        for line in csv.reader(fd, delimiter='\t'):
            # print(line)
            if (line[1] == Investor_Last_Name) & (line[4] == 'P'):  # Define filing type P as public
                # try:
                    # print(line)
                doc_id = line[8]
                date = line[7]
                print(date, doc_id)
                disclosure_doc = fitz.open('{}.pdf'.format(doc_id))

                page = disclosure_doc.load_page(page_id=0)

                json_data = page.get_text('json')
                json_data = json.loads(json_data)
                # print(json_data.keys())

                for block in json_data['blocks']:
                    # print(block)
                    if 'lines' in block:
                        i = 0
                        for item in block['lines'][0]['spans']:
                            if 'ESCRIPTION' in item['text']: # Use discription to locate the transaction detail, only works for recent reports
                                print(item['text'])
                                print(block['lines'][0]['spans'][i+1]['text'])
                            i += 1
                # except:
                #     pass
    year += 1

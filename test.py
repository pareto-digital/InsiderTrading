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
                        if 'ESCRIPTION' in item['text']:  # Use discription to locate the transaction detail
                            print(item['text'])
                            print(block['lines'][0]['spans'][i + 1]['text'])
                        i += 1
            # except:
            #     pass

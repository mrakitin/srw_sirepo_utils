import json
from pprint import pprint


def read_json(json_file='in.json'):
    content = None

    with open(json_file, 'r') as fin:
        with open('in_pprint.json', 'w') as fout:
            content = json.loads(fin.read())
            pprint(content, stream=fout)

    return content


if __name__ == "__main__":
    content = read_json()

    print ''

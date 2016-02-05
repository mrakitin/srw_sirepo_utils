import json


def read_json(json_file='in.json'):
    content = None

    save_file = 'in_pprint.json'
    with open(json_file, 'r') as fin:
        with open(save_file, 'w') as fout:
            json.dump(
                json.loads(fin.read()),
                fout,
                sort_keys=True,
                indent=4,
                separators=(',', ': '),
            )

    return content


if __name__ == "__main__":
    content = read_json()

    print ''

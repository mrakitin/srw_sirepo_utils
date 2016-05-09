import json


def convert_json(infile='in.json', outfile=None):
    if not outfile:
        outfile = infile
    with open(infile, 'r') as fin:
        content = fin.read()
        with open(outfile, 'w') as fout:
            json.dump(
                json.loads(content),
                fout,
                sort_keys=True,
                indent=4,
                separators=(',', ': '),
            )

    return content, outfile


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Convert JSON file to a readable JSON.')
    parser.add_argument('-i', '--input_file', dest='infile', help='input JSON file.')
    parser.add_argument('-o', '--output_file', dest='outfile', help='output JSON file.')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='enable debug information.')

    args = parser.parse_args()
    infile = args.infile
    outfile = args.outfile
    debug = args.debug

    if infile and os.path.isfile(infile):
        content, outfile_real = convert_json(infile=infile, outfile=outfile)
        if content:
            print('\nConverted successfully:\n    <{}> -> <{}>.'.format(infile, outfile_real))
        else:
            print('Failed to convert!')

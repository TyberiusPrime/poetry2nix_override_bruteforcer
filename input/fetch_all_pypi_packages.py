import urllib.request
import re
import json
from pathlib import Path


if __name__ == '__main__':
    print('Getting list of all PyPI packages ... ', end='', flush=True)
    html = urllib.request.urlopen('https://pypi.org/simple/').read().decode('utf-8')
    pattern = re.compile(r'>([^<]+)</a>')
    all_packages = [match[1] for match in re.finditer(pattern, html)]
    print(f'Found {len(all_packages):,} packages\n')
    Path('all_pypi_packages.json').write_text(json.dumps(all_packages))

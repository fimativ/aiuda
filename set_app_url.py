"""Update only local workshop hyperlinks in a PPTX, preserving the source file."""
import argparse
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.etree import ElementTree as ET
from urllib.parse import urlparse
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('presentation',type=Path);p.add_argument('public_url');p.add_argument('--output',type=Path)
a=p.parse_args();u=urlparse(a.public_url)
if u.scheme!='https' or not u.hostname:raise SystemExit('Use the verified public HTTPS app URL.')
out=a.output or a.presentation.with_stem(a.presentation.stem+'_public_link')
if out.resolve()==a.presentation.resolve():raise SystemExit('Output must differ from the original.')
count=0
with ZipFile(a.presentation) as source,ZipFile(out,'w',ZIP_DEFLATED) as target:
    for info in source.infolist():
        data=source.read(info.filename)
        if info.filename.endswith('.rels'):
            tree=ET.fromstring(data);changed=False
            for relation in tree:
                if relation.get('Target') in ('http://localhost:8501','http://127.0.0.1:8501'):
                    relation.set('Target',a.public_url);count+=1;changed=True
            if changed:data=ET.tostring(tree,encoding='utf-8',xml_declaration=True)
        target.writestr(info,data)
print(f'Updated {count} workshop links in {out}')

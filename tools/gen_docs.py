"""Regenerate docs/TEMPLATES.md from the template classes: python tools/gen_docs.py"""
import sys, os, json, inspect
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fpm.templates import REGISTRY

out = ['# Template reference', '', 'Generated from the code by `tools/gen_docs.py`. Time params accept anchors (see README).', '',
       '![catalog](../library.png)', '']
for name, c in REGISTRY.items():
    out += [f'## `{name}`', '', inspect.cleandoc(c.__doc__ or ''), '']
    out.append(f'* default background: `{c.bg_default}`  ·  consumes previous card: `{c.takes_prev}`')
    if c.TIMES: out.append('* time params: ' + ', '.join(f'`{t}`' for t in c.TIMES))
    if c.DEFAULTS:
        out.append('* params and defaults:')
        for k, v in c.DEFAULTS.items(): out.append(f'  * `{k}`: `{json.dumps(v)}`')
    out.append('')
os.makedirs('docs', exist_ok=True)
open('docs/TEMPLATES.md', 'w').write('\n'.join(out)); print('wrote docs/TEMPLATES.md')

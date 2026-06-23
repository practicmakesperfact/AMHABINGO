import re
import glob

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if '──' in content:
        # Remove box-drawing characters from comments
        updated = re.sub(r'/\* ── (.+?) ──* \*/', r'/* \1 */', content)
        updated = re.sub(r'\{/\* ── (.+?) ──* \*/\}', r'{/* \1 */}', updated)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(updated)
        print(f'Fixed: {path}')
        return True
    return False

files = glob.glob('frontend/app/**/*.tsx', recursive=True)
count = sum(1 for f in files if fix_file(f))
print(f'Total fixed: {count} files')

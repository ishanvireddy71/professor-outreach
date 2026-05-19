
import os
import glob

print("=== TEMPLATES FOLDER CHECK ===")
print("Current directory:", os.getcwd())
print()

# Check if templates folder exists
if os.path.exists('templates'):
    files = os.listdir('templates')
    print(f"Files in templates/ ({len(files)} files):")
    for f in sorted(files):
        path = os.path.join('templates', f)
        size = os.path.getsize(path)
        # Check for base target blank
        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read(5000)  # read first 5000 chars
        has_base = '<base' in content
        has_blank = 'target="_blank"' in content
        status = "❌ OLD (has base/blank)" if (has_base or has_blank) else "✅ NEW"
        print(f"  {f:25s} {size:6,} bytes  {status}")
else:
    print("❌ templates/ folder NOT FOUND")

print()
print("=== CHECKING FOR base.html ===")
if os.path.exists('templates/base.html'):
    print("✅ base.html exists")
else:
    print("❌ base.html MISSING — you need to add it")

print()
print("=== RECOMMENDATION ===")
print("If you see ❌ OLD files, you need to REPLACE them with the new ones I gave you.")
print("Delete the old files and copy the new downloaded files into templates/")
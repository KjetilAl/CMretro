import re

with open("ui_pygame.py", "r") as f:
    content = f.read()

# Replace pygame.font.SysFont sizes
content = re.sub(r'SysFont\("Courier New", 9', 'SysFont("Courier New", 13', content)
content = re.sub(r'SysFont\("Courier New", 11', 'SysFont("Courier New", 15', content)
content = re.sub(r'SysFont\("Courier New", 14', 'SysFont("Courier New", 20', content)
content = re.sub(r'SysFont\("Courier New", 18', 'SysFont("Courier New", 26', content)

# Replace fallback Font sizes
content = re.sub(r'Font\(None, 10\)', 'Font(None, 15)', content)
content = re.sub(r'Font\(None, 12\)', 'Font(None, 18)', content)
content = re.sub(r'Font\(None, 16\)', 'Font(None, 24)', content)
content = re.sub(r'Font\(None, 20\)', 'Font(None, 30)', content)

with open("ui_pygame.py", "w") as f:
    f.write(content)

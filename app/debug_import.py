import reveal_dashboard
print("Arquivo importado:", reveal_dashboard.__file__)
print("Tem render?", hasattr(reveal_dashboard, "render"))
print("Dir (top 20):", list(dir(reveal_dashboard))[:20])

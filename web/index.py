import glob

base = """
<html>
<head>
	<title>GATD On Inductor Webpages</title>
</head>
</body>
	<h1>Pages on Inductor</h1>

	<ul>
"""

end = """
	</ul>
</body>
</html>
"""


index = open('index.html', 'w')
index.write(base)


htmls = glob.glob('*.html')

for html in sorted(htmls):
	index.write('<li><a href="{page}">{page}</a></li>\n'.format(page=html))

index.write(end)
index.close()

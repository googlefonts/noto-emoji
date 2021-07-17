import os

with open("CHANGES_NEW.md", 'w') as changes:
	for svg in os.listdir('derived'):
		changes.write("| ![{}](https://raw.githubusercontent.com/C1710/blobmoji/main/svg/{}) | [`svg/{}`](svg/{}) |\n".format(svg[:-4], svg.replace(' ', '%20'), svg, svg.replace(' ', '%20')))
		# We'll delete the contents as well, as we don't need it
		with open('derived/{}'.format(svg), 'w') as derived:
			derived.write('')
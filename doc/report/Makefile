TEX = tfe
PDF = $(TEX).pdf

.PHONY: all build clean distclean

all: build

build:
	pdflatex $(TEX)
	bibtex $(TEX)
	pdflatex $(TEX)
	pdflatex $(TEX)

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot

distclean: clean
	rm -f $(PDF)
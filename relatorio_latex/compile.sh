#!/bin/bash
cd /Users/rodrigofregonasse/Developer/PSP3/relatorio_latex
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

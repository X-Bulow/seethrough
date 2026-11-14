# Build the final report.
#
#   make            build/asg2-final-Cheng_Zefeng+Wei_Yuning+Xu_Ruofan.pdf (latexmk, outputs in build/)
#   make tables     regenerate tables/*.tex and tables/*.dat from the committed results bundles
#   make watch      rebuild on every save
#   make clean      remove LaTeX intermediates from build/, keep the PDF
#   make distclean  empty build/
#
# Sources are in src/ (main.tex and one file per section); figures/ and tables/ are generated
# (benchmarks/plot.py, scripts/gen.py) and never edited by hand. Run from this directory.
LATEXMK ?= latexmk
PYTHON  ?= python3
NAME    := asg2-final-Cheng_Zefeng+Wei_Yuning+Xu_Ruofan
OUT     := build
FLAGS   := -pdf -outdir=$(OUT) -interaction=nonstopmode -halt-on-error -file-line-error

SRCS    := $(wildcard src/*.tex) src/refs.bib
TABLES  := $(wildcard tables/*.tex tables/*.dat)
FIGURES := $(wildcard figures/*.pdf)

.PHONY: all tables watch clean distclean
all: $(OUT)/$(NAME).pdf

$(OUT)/main.pdf: $(SRCS) $(TABLES) $(FIGURES) Makefile
	$(LATEXMK) $(FLAGS) src/main.tex

$(OUT)/$(NAME).pdf: $(OUT)/main.pdf
	cp $< $@

tables:
	$(PYTHON) scripts/gen.py

watch:
	$(LATEXMK) $(FLAGS) -pvc src/main.tex

clean:
	$(LATEXMK) -c -outdir=$(OUT) src/main.tex

distclean:
	find $(OUT) -mindepth 1 ! -name .gitkeep -delete

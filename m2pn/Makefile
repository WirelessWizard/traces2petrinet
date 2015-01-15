PYTHON = "python"
PARSER = "m2pn.py"
MODELS_DIR = "./models/"
OUTPUT_DIR = "./output/"
MODELS = $(wildcard models/*.m)
OUTPUT = $(addprefix output/,$(notdir $(MODELS:.m=.pdf)))

all: hello $(OUTPUT)
	@echo 'All predicate inputs successfully parsed.'

hello:
	@echo 'Starting the M2PN parser...'
	@echo $(MODELS_DIR)
	@echo $(MODELS)
	@echo $(OUTPUT)
	@mkdir -p $(OUTPUT_DIR)

output/%.pdf: models/%.m
	$(PYTHON) $(PARSER) -if $< -of $@

clean:
	@rm -r $(OUTPUT_DIR)

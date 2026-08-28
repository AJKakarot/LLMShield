PY = ./.venv/Scripts/python.exe

.PHONY: docker-build docker-demo docker-demo-run docker-demo-fast phase2-up phase2-down demo demo-fast poc poc-fast capture diagram deck present freeze

docker-build:   ## Build the image (bakes both models in, ~2.2GB, takes a few min)
	docker compose build poc

docker-demo:    ## PREFERRED live demo: steps through on Enter, no network
	docker compose run --rm poc --pause

docker-demo-run: ## Same but runs straight through without pausing
	docker compose run --rm poc

docker-demo-fast: ## Same but keyword stand-in, ~3s
	docker compose run --rm poc --fast

phase2-up:      ## Start Qdrant + Redis (Phase 2 infrastructure)
	docker compose --profile phase2 up -d qdrant redis

phase2-down:
	docker compose --profile phase2 down

demo:           ## Host-Python demo (needs the venv): real deberta filter, fully offline, no noise
	HF_HUB_OFFLINE=1 $(PY) poc_bypass.py

demo-fast:      ## Fallback if anything is wrong with the model cache (~5s)
	HF_HUB_OFFLINE=1 $(PY) poc_bypass.py --fast

poc:            ## Same as demo but allowed to reach the network (first run)
	$(PY) poc_bypass.py

poc-fast:
	$(PY) poc_bypass.py --fast

capture:        ## Re-record the run the deck quotes from
	HF_HUB_OFFLINE=1 $(PY) poc_bypass.py > docs/captures/demo-output.txt 2>&1
	sed -i 's/\r$$//' docs/captures/demo-output.txt

MMD = problem flow architecture

diagram:        ## every mermaid source -> png, light for print + dark for the deck
	@for d in $(MMD); do 	  npx -y @mermaid-js/mermaid-cli -i docs/$$d.mmd -o docs/$$d.png -b white -w 1800; 	  npx -y @mermaid-js/mermaid-cli -i docs/$$d.mmd -o docs/captures/$$d-dark.png -t dark -b transparent -w 2000 -s 2; 	done

deck:           ## Rebuild docs/deck.html from the template + the captured run
	$(PY) docs/build_deck.py

present:        ## Serve the deck at http://127.0.0.1:8777/deck.html
	@echo "Open http://127.0.0.1:8777/deck.html  (Ctrl-C to stop)"
	cd docs && $(CURDIR)/.venv/Scripts/python.exe -m http.server 8777 --bind 127.0.0.1

freeze:
	$(PY) -m pip freeze > requirements-lock.txt

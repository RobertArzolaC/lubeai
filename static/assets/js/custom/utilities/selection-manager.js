class SelectionManager {
    constructor(storageKey, availableOptions = [], elementTag = "") {
        this.storageKey = storageKey;
        this.elementTag = elementTag;
        this.availableOptions = availableOptions;
        this.selections = this.loadSelections();
    }

    loadSelections() {
        const savedSelections = localStorage.getItem(this.storageKey);
        return savedSelections ? JSON.parse(savedSelections) : [];
    }

    saveSelections() {
        localStorage.setItem(this.storageKey, JSON.stringify(this.selections));
        this.updateCounters();
    }

    addSelection(selection) {
        if (!this.selections.includes(selection)) {
            this.selections.push(selection);
            this.saveSelections();
        }
    }

    removeSelection(selection) {
        const index = this.selections.indexOf(selection);
        if (index > -1) {
            this.selections.splice(index, 1);
            this.saveSelections();
        }
    }

    clearSelections() {
        this.selections = [];
        localStorage.removeItem(this.storageKey);
        this.updateCounters();
    }

    getSelections() {
        return this.selections;
    }

    getSelectionCount() {
        return this.selections.length;
    }

    selectAll() {
        this.selections = [...this.availableOptions];
        this.saveSelections();
    }

    updateAvailableOptions(newOptions) {
        this.availableOptions = newOptions;
        this.selections = this.selections.filter(selection =>
            this.availableOptions.includes(selection)
        );
        this.saveSelections();
    }

    isSelected(option) {
        return this.selections.includes(option);
    }

    isSelectedAll() {
        return this.selections.length === this.availableOptions.length;
    }

    updateCounters() {
        const testsCounter = document.getElementById(this.elementTag);
        if (testsCounter) {
            testsCounter.textContent = this.getSelectionCount();
        }
    }
}

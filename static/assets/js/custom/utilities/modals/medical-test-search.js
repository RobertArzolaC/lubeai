"use strict";

var KTModalMedicalTestSearch = function () {
    var element;
    var resultsElement;
    var wrapperElement;
    var emptyElement;
    var searchObject;

    var processs = function (search) {
        console.log("search", search);
        var timeout = setTimeout(function () {
            var number = KTUtil.getRandomInt(1, 3);

            if (number === 3) {
                resultsElement.classList.add('d-none');
                emptyElement.classList.remove('d-none');
            } else {
                resultsElement.classList.remove('d-none');
                emptyElement.classList.add('d-none');
            }

            search.complete();
        }, 1500);
    }

    var clear = function (search) {
        resultsElement.classList.add('d-none');
        emptyElement.classList.add('d-none');
    }

    return {
        init: function () {
            element = document.querySelector('#kt_modal_medical_test_search_handler');

            if (!element) {
                return;
            }

            wrapperElement = element.querySelector('[data-kt-search-element="wrapper"]');
            resultsElement = element.querySelector('[data-kt-search-element="results"]');
            emptyElement = element.querySelector('[data-kt-search-element="empty"]');

            searchObject = new KTSearch(element);

            searchObject.on('kt.search.process', processs);

            searchObject.on('kt.search.clear', clear);
        }
    };
}();

KTUtil.onDOMContentLoaded(function () {
    KTModalMedicalTestSearch.init();
});

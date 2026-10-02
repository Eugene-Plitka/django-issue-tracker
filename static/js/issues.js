const form = document.getElementById("issue-filters-form");
const searchInput = document.getElementById("q");
const autoSubmitFields = document.querySelectorAll(".auto-submit");

if (form) {
    autoSubmitFields.forEach((field) => {
        field.addEventListener("change", () => {
            form.submit();
        });
    });

    if (searchInput) {
        let searchTimer;

        searchInput.addEventListener("input", () => {
            clearTimeout(searchTimer);

            searchTimer = setTimeout(() => {
                form.submit();
            }, 500);
        });
    }
}
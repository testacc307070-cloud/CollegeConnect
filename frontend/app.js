/* =========================================================
   COLLEGECONNECT FRONTEND
   ========================================================= */

let allDistricts = [];
let allBranches = [];
let allColleges = [];

let selectedDistricts = [];
let selectedBranches = [];
let selectedCollege = null;

let latestResults = [];
let latestPredictionData = null;
let activeResultFilter = "ALL";

let choices = loadSavedChoices();

let aiSuggestedChoices = [];

let draggedChoiceIndex = null;
let draggedAIChoiceIndex = null;

/* =========================================================
   HELPERS / DOM
========================================================= */

function byId(id) {
    return document.getElementById(id);
}

const navTabs =
    document.querySelectorAll(".nav-tab");

const predictorTab =
    byId("predictorTab");

const optimizerTab =
    byId("optimizerTab");

const matrixTab =
    byId("matrixTab");

const predictionForm =
    byId("predictionForm");

const cutoffInput =
    byId("cutoffMark");

const stateRankInput =
    byId("stateRank");

const communitySelect =
    byId("community");

const counselingQuotaSelect =
    byId("counselingQuota");

const quotaAdvisoryBanner =
    byId("quotaAdvisoryBanner");

const quotaAdvisoryTitle =
    byId("quotaAdvisoryTitle");

const quotaAdvisoryDesc =
    byId("quotaAdvisoryDesc");

const tierFilterSelect =
    byId("tierFilter");

const clearButton =
    byId("clearButton");

const toggleCalcButton =
    byId("toggleCalcButton");

const calculatorPanel =
    byId("calculatorPanel");

const mathsMarksInput =
    byId("mathsMarks");

const physicsMarksInput =
    byId("physicsMarks");

const chemistryMarksInput =
    byId("chemistryMarks");

const applyCutoffButton =
    byId("applyCutoffButton");

const calcPreviewDisplay =
    byId("calcPreviewDisplay");


const districtSearch =
    byId("districtSearch");

const districtSearchButton =
    byId("districtSearchButton");

const districtOptions =
    byId("districtOptions");

const selectedDistrictsContainer =
    byId("selectedDistricts");

const districtCount =
    byId("districtCount");

const clearDistrictsButton =
    byId("clearDistricts");

const branchSearch =
    byId("branchSearch");

const branchSearchButton =
    byId("branchSearchButton");

const branchOptions =
    byId("branchOptions");

const selectedBranchesContainer =
    byId("selectedBranches");

const branchCount =
    byId("branchCount");

const clearBranchesButton =
    byId("clearBranches");

const collegeSearch =
    byId("collegeSearch");

const collegeSearchButton =
    byId("collegeSearchButton");

const collegeSuggestions =
    byId("collegeSuggestions");

const collegeSelectedDisplay =
    byId("collegeSelectedDisplay");

const loading =
    byId("loading");

const errorMessage =
    byId("errorMessage");

const resultsSection =
    byId("resultsSection");

const resultsSummary =
    byId("resultsSummary");

const resultCount =
    byId("resultCount");

const resultDistribution =
    byId("resultDistribution");

const resultsList =
    byId("resultsList");

const resultFilterButtons =
    document.querySelectorAll(
        ".result-filter-btn"
    );

const ragSection =
    byId("ragSection");

const ragLoading =
    byId("ragLoading");

const ragError =
    byId("ragError");

const ragContent =
    byId("ragContent");

const ragModelBadge =
    byId("ragModelBadge");

const ragSubtitle =
    byId("ragSubtitle");

const openOptimizerButton =
    byId("openOptimizerButton");

const emptyChoices =
    byId("emptyChoices");

const choicesContainer =
    byId("choicesContainer");

const exportButton =
    byId("exportButton");

const exportPdfButton =
    byId("exportPdfButton");

const exportDoteButton =
    byId("exportDoteButton");

const clearChoicesButton =

    byId("clearChoicesButton");

const matrixCommunity =
    byId("matrixCommunity");

const matrixDistrict =
    byId("matrixDistrict");

const matrixBranch =
    byId("matrixBranch");

const matrixCollege =
    byId("matrixCollege");

const loadMatrixButton =
    byId("loadMatrixButton");

const matrixLoading =
    byId("matrixLoading");

const matrixError =
    byId("matrixError");

const matrixSection =
    byId("matrixSection");

const matrixTableBody =
    byId("matrixTableBody");

const themeToggleBtn =
    byId("themeToggleBtn");

const themeToggleIcon =
    byId("themeToggleIcon");

const themeToggleText =
    byId("themeToggleText");

/* =========================================================
   THEME SWITCHING (DARK / LIGHT)
========================================================= */

const THEME_STORAGE_KEY = "collegeconnect_theme";
let currentTrendData = null;

function applyTheme(theme, persist = true) {
    const isLight = theme === "light";
    if (isLight) {
        document.documentElement.setAttribute("data-theme", "light");
        if (themeToggleIcon) themeToggleIcon.textContent = "☀️";
        if (themeToggleText) themeToggleText.textContent = "Light";
        if (themeToggleBtn) themeToggleBtn.setAttribute("aria-label", "Switch to dark theme");
    } else {
        document.documentElement.removeAttribute("data-theme");
        if (themeToggleIcon) themeToggleIcon.textContent = "🌙";
        if (themeToggleText) themeToggleText.textContent = "Dark";
        if (themeToggleBtn) themeToggleBtn.setAttribute("aria-label", "Switch to light theme");
    }

    if (persist) {
        try {
            localStorage.setItem(THEME_STORAGE_KEY, theme);
        } catch (e) {
            console.warn("Could not save theme preference:", e);
        }
    }

    // Refresh dynamic lists and active modal chart if open
    renderChoices();
    renderAISuggestedList();
    if (currentTrendData && trendModal && !trendModal.classList.contains("hidden")) {
        renderTrendSvgChart(currentTrendData.rows, currentTrendData.validRecords);
    }
}

function initTheme() {
    let savedTheme = "dark";
    try {
        savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || "dark";
    } catch (e) {
        savedTheme = "dark";
    }

    applyTheme(savedTheme, false);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const current = document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
            const nextTheme = current === "light" ? "dark" : "light";
            applyTheme(nextTheme, true);
        });
    }
}

/* =========================================================
   INITIALIZATION
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        initTheme();

        createOptimizerControls();

        renderDistrictPicker();

        renderBranchPicker();

        renderCollegeSuggestions();

        renderSelectedCollege();

        renderChoices();

        await loadDistricts();

        renderDistrictPicker();

        await loadBranches();

        renderBranchPicker();

        await loadColleges();

        renderCollegeSuggestions();

        await loadMatrixDistricts();

        await loadMatrixBranches();

        await loadMatrixColleges();

        renderChoices();

        renderAISuggestedList();

    }
);

/* =========================================================
   NAVIGATION
========================================================= */

navTabs.forEach(
    tab => {

        tab.addEventListener(
            "click",
            () => {

                const target =
                    tab.dataset.tab;

                navTabs.forEach(
                    item => {

                        item.classList.remove(
                            "active"
                        );

                    }
                );

                tab.classList.add(
                    "active"
                );

                predictorTab.classList.remove(
                    "active"
                );

                optimizerTab.classList.remove(
                    "active"
                );

                matrixTab.classList.remove(
                    "active"
                );

                if (
                    target ===
                    "predictor"
                ) {

                    predictorTab.classList.add(
                        "active"
                    );

                }

                if (
                    target ===
                    "optimizer"
                ) {

                    optimizerTab.classList.add(
                        "active"
                    );

                    renderChoices();

                    renderAISuggestedList();

                }

                if (
                    target ===
                    "matrix"
                ) {

                    matrixTab.classList.add(
                        "active"
                    );

                }

                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });

            }
        );

    }
);

/* =========================================================
   QUERY PARAMETER HELPER
========================================================= */

function appendMultipleParams(
    params,
    name,
    values
) {

    if (
        !Array.isArray(
            values
        )
    ) {

        return;

    }

    values.forEach(
        value => {

            if (
                value !== null &&
                value !== undefined &&
                String(
                    value
                ).trim() !== ""
            ) {

                params.append(
                    name,
                    String(
                        value
                    )
                );

            }

        }
    );

}

/* =========================================================
   DISTRICTS
========================================================= */

async function loadDistricts() {

    try {

        const response =
            await fetch(
                "/api/districts"
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            data.status !== "ok"
        ) {

            throw new Error(
                data.message ||
                "Failed to load districts."
            );

        }

        allDistricts =
            Array.isArray(
                data.districts
            )
                ? data.districts
                : [];

    } catch (
        error
    ) {

        showError(
            "Could not load districts: " +
            error.message
        );

    }

}

function renderDistrictPicker() {

    if (
        !districtOptions
    ) {

        return;

    }

    const query =
        districtSearch
            ? districtSearch.value
                .trim()
                .toLowerCase()
            : "";

    const filtered =
        allDistricts.filter(
            district =>
                String(
                    district
                )
                    .toLowerCase()
                    .includes(
                        query
                    )
        );

    districtOptions.innerHTML =
        "";

    if (
        filtered.length ===
        0
    ) {

        districtOptions.innerHTML = `
            <div class="picker-empty">
                No districts found.
            </div>
        `;

    } else {

        filtered.forEach(
            district => {

                const row =
                    document.createElement(
                        "div"
                    );

                const isSelected =
                    selectedDistricts.includes(
                        district
                    );

                row.className =
                    "picker-option" +
                    (
                        isSelected
                            ? " selected"
                            : ""
                    );

                row.innerHTML = `
                    <span class="picker-check"></span>

                    <span>
                        ${escapeHtml(
                            district
                        )}
                    </span>
                `;

                row.addEventListener(
                    "click",
                    async () => {

                        toggleDistrict(
                            district
                        );

                        renderDistrictPicker();

                        await loadBranches();

                        renderBranchPicker();

                        await loadColleges();

                        renderCollegeSuggestions();

                    }
                );

                districtOptions.appendChild(
                    row
                );

            }
        );

    }

    renderDistrictChips();

}

function toggleDistrict(
    district
) {

    const index =
        selectedDistricts.indexOf(
            district
        );

    if (
        index >= 0
    ) {

        selectedDistricts.splice(
            index,
            1
        );

    } else {

        selectedDistricts.push(
            district
        );

    }

}

function renderDistrictChips() {

    if (
        !selectedDistrictsContainer
    ) {

        return;

    }

    selectedDistrictsContainer.innerHTML =
        "";

    if (
        selectedDistricts.length ===
        0
    ) {

        districtCount.textContent =
            "No districts selected";

        return;

    }

    districtCount.textContent =
        `${selectedDistricts.length} district${
            selectedDistricts.length ===
            1
                ? ""
                : "s"
        } selected`;

    selectedDistricts.forEach(
        district => {

            const chip =
                document.createElement(
                    "div"
                );

            chip.className =
                "selected-chip";

            chip.innerHTML = `
                <span>
                    ${escapeHtml(
                        district
                    )}
                </span>

                <button
                    type="button"
                    aria-label="Remove district"
                >
                    ×
                </button>
            `;

            chip
                .querySelector(
                    "button"
                )
                .addEventListener(
                    "click",
                    async () => {

                        selectedDistricts =
                            selectedDistricts.filter(
                                item =>
                                    item !==
                                    district
                            );

                        renderDistrictPicker();

                        await loadBranches();

                        renderBranchPicker();

                        await loadColleges();

                        renderCollegeSuggestions();

                    }
                );

            selectedDistrictsContainer
                .appendChild(
                    chip
                );

        }
    );

}

districtSearch?.addEventListener(
    "input",
    () => {

        renderDistrictPicker();

    }
);

districtSearchButton?.addEventListener(
    "click",
    () => {

        renderDistrictPicker();

    }
);

clearDistrictsButton?.addEventListener(
    "click",
    async () => {

        selectedDistricts =
            [];

        renderDistrictPicker();

        await loadBranches();

        renderBranchPicker();

        await loadColleges();

        renderCollegeSuggestions();

    }
);

/* =========================================================
   BRANCHES
========================================================= */

async function loadBranches() {

    try {

        const params =
            new URLSearchParams();

        appendMultipleParams(
            params,
            "district",
            selectedDistricts
        );

        const query =
            params.toString();

        const url =
            query
                ? `/api/branches?${query}`
                : "/api/branches";

        const response =
            await fetch(
                url
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            data.status !== "ok"
        ) {

            throw new Error(
                data.message ||
                "Failed to load branches."
            );

        }

        allBranches =
            Array.isArray(
                data.branches
            )
                ? data.branches
                : [];

        const available =
            new Set(
                allBranches.map(
                    branch =>
                        String(
                            branch.branch_code
                        )
                )
            );

        selectedBranches =
            selectedBranches.filter(
                code =>
                    available.has(
                        String(
                            code
                        )
                    )
            );

    } catch (
        error
    ) {

        showError(
            "Could not load branches: " +
            error.message
        );

    }

}

function renderBranchPicker() {

    if (
        !branchOptions
    ) {

        return;

    }

    const query =
        branchSearch
            ? branchSearch.value
                .trim()
                .toLowerCase()
            : "";

    const filtered =
        allBranches.filter(
            branch => {

                const text =
                    `${branch.branch_code} ${branch.branch_name}`
                        .toLowerCase();

                return text.includes(
                    query
                );

            }
        );

    branchOptions.innerHTML =
        "";

    if (
        filtered.length ===
        0
    ) {

        branchOptions.innerHTML = `
            <div class="picker-empty">
                No branches / courses found.
            </div>
        `;

    } else {

        filtered.forEach(
            branch => {

                const code =
                    String(
                        branch.branch_code
                    );

                const isSelected =
                    selectedBranches.some(
                        value =>
                            String(
                                value
                            ) ===
                            code
                    );

                const row =
                    document.createElement(
                        "div"
                    );

                row.className =
                    "picker-option" +
                    (
                        isSelected
                            ? " selected"
                            : ""
                    );

                row.innerHTML = `
                    <span class="picker-check"></span>

                    <span>
                        ${escapeHtml(
                            code
                        )}
                        -
                        ${escapeHtml(
                            branch.branch_name
                        )}
                    </span>
                `;

                row.addEventListener(
                    "click",
                    async () => {

                        toggleBranch(
                            code
                        );

                        renderBranchPicker();

                        await loadColleges();

                        renderCollegeSuggestions();

                    }
                );

                branchOptions.appendChild(
                    row
                );

            }
        );

    }

    renderBranchChips();

}

function toggleBranch(
    branchCode
) {

    const normalized =
        String(
            branchCode
        );

    const index =
        selectedBranches.findIndex(
            value =>
                String(
                    value
                ) ===
                normalized
        );

    if (
        index >= 0
    ) {

        selectedBranches.splice(
            index,
            1
        );

    } else {

        selectedBranches.push(
            normalized
        );

    }

}

function renderBranchChips() {

    if (
        !selectedBranchesContainer
    ) {

        return;

    }

    selectedBranchesContainer.innerHTML =
        "";

    if (
        selectedBranches.length ===
        0
    ) {

        branchCount.textContent =
            "No branches selected";

        return;

    }

    branchCount.textContent =
        `${selectedBranches.length} branch${
            selectedBranches.length ===
            1
                ? ""
                : "es"
        } selected`;

    selectedBranches.forEach(
        branchCode => {

            const branch =
                allBranches.find(
                    item =>
                        String(
                            item.branch_code
                        ) ===
                        String(
                            branchCode
                        )
                );

            const label =
                branch
                    ? `${branch.branch_code} - ${branch.branch_name}`
                    : String(
                        branchCode
                    );

            const chip =
                document.createElement(
                    "div"
                );

            chip.className =
                "selected-chip";

            chip.innerHTML = `
                <span>
                    ${escapeHtml(
                        label
                    )}
                </span>

                <button
                    type="button"
                    aria-label="Remove branch"
                >
                    ×
                </button>
            `;

            chip
                .querySelector(
                    "button"
                )
                .addEventListener(
                    "click",
                    async () => {

                        selectedBranches =
                            selectedBranches.filter(
                                value =>
                                    String(
                                        value
                                    ) !==
                                    String(
                                        branchCode
                                    )
                            );

                        renderBranchPicker();

                        await loadColleges();

                        renderCollegeSuggestions();

                    }
                );

            selectedBranchesContainer
                .appendChild(
                    chip
                );

        }
    );

}

branchSearch?.addEventListener(
    "input",
    () => {

        renderBranchPicker();

    }
);

branchSearchButton?.addEventListener(
    "click",
    () => {

        renderBranchPicker();

    }
);

clearBranchesButton?.addEventListener(
    "click",
    async () => {

        selectedBranches =
            [];

        renderBranchPicker();

        await loadColleges();

        renderCollegeSuggestions();

    }
);

/* =========================================================
   COLLEGES
========================================================= */

async function loadColleges() {

    try {

        const params =
            new URLSearchParams();

        appendMultipleParams(
            params,
            "district",
            selectedDistricts
        );

        appendMultipleParams(
            params,
            "branch_code",
            selectedBranches
        );

        const query =
            params.toString();

        const url =
            query
                ? `/api/colleges?${query}`
                : "/api/colleges";

        const response =
            await fetch(
                url
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            data.status !== "ok"
        ) {

            throw new Error(
                data.message ||
                "Failed to load colleges."
            );

        }

        allColleges =
            Array.isArray(
                data.colleges
            )
                ? data.colleges
                : [];

        if (
            selectedCollege
        ) {

            const available =
                allColleges.some(
                    college =>
                        String(
                            college.college_code
                        ) ===
                        String(
                            selectedCollege.college_code
                        )
                );

            if (
                !available
            ) {

                selectedCollege =
                    null;

                renderSelectedCollege();

            }

        }

    } catch (
        error
    ) {

        showError(
            "Could not load colleges: " +
            error.message
        );

    }

}

function renderCollegeSuggestions() {

    if (
        !collegeSuggestions ||
        !collegeSearch
    ) {

        return;

    }

    const query =
        collegeSearch.value
            .trim()
            .toLowerCase();

    const filtered =
        allColleges
            .filter(
                college => {

                    const text =
                        `${college.college_code} ${college.college_name} ${college.district}`
                            .toLowerCase();

                    return text.includes(
                        query
                    );

                }
            )
            .slice(
                0,
                80
            );

    collegeSuggestions.innerHTML =
        "";

    if (
        filtered.length ===
        0
    ) {

        collegeSuggestions.innerHTML = `
            <div class="college-suggestion">
                <div class="college-suggestion-meta">
                    No colleges found.
                </div>
            </div>
        `;

    } else {

        filtered.forEach(
            college => {

                const row =
                    document.createElement(
                        "div"
                    );

                row.className =
                    "college-suggestion";

                row.innerHTML = `
                    <div class="college-suggestion-name">
                        ${escapeHtml(
                            college.college_name
                        )}
                    </div>

                    <div class="college-suggestion-meta">
                        Code:
                        ${escapeHtml(
                            String(
                                college.college_code
                            )
                        )}

                        ·

                        ${escapeHtml(
                            college.district ||
                            "Unknown District"
                        )}
                    </div>
                `;

                row.addEventListener(
                    "click",
                    () => {

                        selectedCollege = {

                            college_code:
                                college.college_code,

                            college_name:
                                college.college_name,

                            district:
                                college.district

                        };

                        collegeSearch.value =
                            college.college_name;

                        renderSelectedCollege();

                        hideCollegeSuggestions();

                    }
                );

                collegeSuggestions
                    .appendChild(
                        row
                    );

            }
        );

    }

    if (
        query
    ) {

        collegeSuggestions.classList.remove(
            "hidden"
        );

    }

}

function renderSelectedCollege() {

    if (
        !collegeSelectedDisplay
    ) {

        return;

    }

    if (
        !selectedCollege
    ) {

        collegeSelectedDisplay.classList.add(
            "hidden"
        );

        collegeSelectedDisplay.innerHTML =
            "";

        return;

    }

    collegeSelectedDisplay.classList.remove(
        "hidden"
    );

    collegeSelectedDisplay.innerHTML = `
        <span>

            Selected:

            <strong>
                ${escapeHtml(
                    selectedCollege.college_name
                )}
            </strong>

            ·

            ${escapeHtml(
                String(
                    selectedCollege.college_code
                )
            )}

        </span>

        <button
            id="removeSelectedCollege"
            type="button"
            aria-label="Remove selected college"
        >
            ×
        </button>
    `;

    byId(
        "removeSelectedCollege"
    )?.addEventListener(
        "click",
        () => {

            selectedCollege =
                null;

            collegeSearch.value =
                "";

            renderSelectedCollege();

            renderCollegeSuggestions();

        }
    );

}

function hideCollegeSuggestions() {

    collegeSuggestions?.classList.add(
        "hidden"
    );

}

collegeSearch?.addEventListener(
    "input",
    () => {

        renderCollegeSuggestions();

    }
);

collegeSearchButton?.addEventListener(
    "click",
    () => {

        renderCollegeSuggestions();

        collegeSuggestions.classList.remove(
            "hidden"
        );

    }
);

document.addEventListener(
    "click",
    event => {

        if (
            !event.target.closest(
                ".college-search-box"
            )
        ) {

            hideCollegeSuggestions();

        }

    }
);

/* =========================================================
   PREDICTION FORM
========================================================= */

predictionForm.addEventListener(
    "submit",
    async event => {

        event.preventDefault();

        hideError();

        hideRagError();

        const cutoffText =
            cutoffInput.value.trim();

        const rankText =
            stateRankInput.value.trim();

        const community =
            communitySelect.value;

        if (
            !cutoffText &&
            !rankText
        ) {

            showError(
                "Please enter either your cutoff mark or your state rank."
            );

            return;

        }

        if (
            cutoffText &&
            rankText
        ) {

            showError(
                "Please enter either Cutoff Mark or State Rank, not both."
            );

            return;

        }

        if (
            !community
        ) {

            showError(
                "Please select your community."
            );

            return;

        }

        if (
            cutoffText
        ) {

            const cutoff =
                Number(
                    cutoffText
                );

            if (
                !Number.isFinite(
                    cutoff
                ) ||
                cutoff <= 0 ||
                cutoff > 200
            ) {

                showError(
                    "Cutoff mark must be greater than 0 and at most 200."
                );

                return;

            }

            await runPrediction(
                "cutoff",
                {

                    cutoffMark:
                        cutoff,

                    community:
                        community,

                    districts:
                        [
                            ...selectedDistricts
                        ],

                    branches:
                        [
                            ...selectedBranches
                        ],

                    collegeCode:
                        selectedCollege
                            ? selectedCollege.college_code
                            : null

                }
            );

            return;

        }

        const rank =
            Number(
                rankText
            );

        if (
            !Number.isInteger(
                rank
            ) ||
            rank <= 0
        ) {

            showError(
                "State rank must be a positive whole number."
            );

            return;

        }

        await runPrediction(
            "rank",
            {

                stateRank:
                    rank,

                community:
                    community,

                districts:
                    [
                        ...selectedDistricts
                    ],

                branches:
                    [
                        ...selectedBranches
                    ],

                collegeCode:
                    selectedCollege
                        ? selectedCollege.college_code
                        : null

            }
        );

    }
);

/* =========================================================
   RUN PREDICTION
========================================================= */

async function runPrediction(
    mode,
    input
) {

    setLoading(
        true
    );

    resultsSection.classList.add(
        "hidden"
    );

    ragSection.classList.add(
        "hidden"
    );

    hideError();

    hideRagError();

    try {

        const params =
            new URLSearchParams();

        if (
            mode ===
            "cutoff"
        ) {

            params.set(
                "cutoff_mark",
                input.cutoffMark
            );

        } else {

            params.set(
                "state_rank",
                input.stateRank
            );

        }

        params.set(
            "community",
            input.community
        );

        appendMultipleParams(
            params,
            "district",
            input.districts
        );

        appendMultipleParams(
            params,
            "branch_code",
            input.branches
        );

        if (
            input.collegeCode
        ) {

            params.set(
                "college_code",
                input.collegeCode
            );

        }

        const quotaVal =
            counselingQuotaSelect?.value ||
            "GENERAL";

        params.set(
            "quota",
            quotaVal
        );

        const tierVal =
            tierFilterSelect?.value ||
            "ALL";

        if (
            tierVal &&
            tierVal !== "ALL"
        ) {

            params.set(
                "tier",
                tierVal
            );

        }

        params.set(
            "limit",
            "30"
        );

        const endpoint =
            mode ===
            "cutoff"
                ? "/api/predictions"
                : "/api/rank-predictions";

        const response =
            await fetch(
                `${endpoint}?${params.toString()}`
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            data.status !== "ok"
        ) {

            throw new Error(
                data.message ||
                "Prediction request failed."
            );

        }

        latestPredictionData =
            data;

        latestResults =
            Array.isArray(
                data.predictions
            )
                ? data.predictions
                : [];

        generateAISuggestedList();

        activeResultFilter =
            "ALL";

        updateResultFilterButtons(
            "ALL"
        );

        renderResults(
            data
        );

        await loadRagExplanation(
            mode,
            input
        );

    } catch (
        error
    ) {

        showError(
            error.message ||
            "Prediction request failed."
        );

    } finally {

        setLoading(
            false
        );

    }

}

/* =========================================================
   RESULTS
========================================================= */

function renderResults(
    data
) {

    const mode =
        data.mode ||
        "cutoff";

    const input =
        data.student_input ||
        {};

    const counts =
        data.result_counts ||
        calculateDisplayedCounts(
            latestResults
        );

    const filtered =
        getFilteredResults();

    let summary =
        "";

    if (
        mode ===
        "cutoff"
    ) {

        summary =
            `Historical options for cutoff ${
                input.cutoff_mark ??
                "—"
            } and community ${
                input.community ??
                "—"
            }.`;

    } else {

        summary =
            `Historical options for state rank ${
                input.state_rank ??
                "—"
            } and community ${
                input.community ??
                "—"
            }.`;

    }

    const districts =
        Array.isArray(
            input.district
        )
            ? input.district
            : [];

    const branches =
        Array.isArray(
            input.branch_code
        )
            ? input.branch_code
            : [];

    if (
        districts.length >
        0
    ) {

        summary +=
            ` Districts: ${
                districts.join(
                    ", "
                )
            }.`;

    }

    if (
        branches.length >
        0
    ) {

        summary +=
            ` Branches: ${
                branches.join(
                    ", "
                )
            }.`;

    }

    if (
        input.college_code
    ) {

        summary +=
            ` Specific college selected: ${
                input.college_code
            }.`;

    }

    summary +=
        ` Showing ${
            latestResults.length
        } relevant option${
            latestResults.length ===
            1
                ? ""
                : "s"
        }.`;

    resultsSummary.textContent =
        summary;

    resultCount.textContent =
        `${
            filtered.length
        } option${
            filtered.length ===
            1
                ? ""
                : "s"
        }`;

    resultDistribution.innerHTML = `
        <span class="
            distribution-pill
            distribution-safe
        ">
            🛡 Safe:
            ${counts.Safe ?? 0}
        </span>

        <span class="
            distribution-pill
            distribution-target
        ">
            🎯 Target:
            ${counts.Target ?? 0}
        </span>

        <span class="
            distribution-pill
            distribution-reach
        ">
            🔥 Reach:
            ${counts.Reach ?? 0}
        </span>
    `;

    resultsList.innerHTML =
        "";

    if (
        filtered.length ===
        0
    ) {

        resultsList.innerHTML = `
            <div class="no-results">
                No results in this category.

                <br><br>

                Select
                <strong>All</strong>
                or another category.
            </div>
        `;

        resultsSection.classList.remove(
            "hidden"
        );

        return;

    }

    filtered.forEach(
        result => {

            resultsList.appendChild(
                createResultCard(
                    result
                )
            );

        }
    );

    resultsSection.classList.remove(
        "hidden"
    );

}

function calculateDisplayedCounts(
    results
) {

    const counts = {

        Reach:
            0,

        Target:
            0,

        Safe:
            0

    };

    results.forEach(
        result => {

            const tier =
                normalizeTier(
                    result.tier
                );

            if (
                tier
            ) {

                counts[
                    tier
                ] +=
                    1;

            }

        }
    );

    return counts;

}

function getFilteredResults() {

    if (
        activeResultFilter ===
        "ALL"
    ) {

        return [
            ...latestResults
        ];

    }

    return latestResults.filter(
        result =>
            normalizeTier(
                result.tier
            ) ===
            activeResultFilter
    );

}

function normalizeTier(
    tier
) {

    if (
        tier ===
            null ||
        tier ===
            undefined
    ) {

        return null;

    }

    const value =
        String(
            tier
        )
            .trim()
            .toLowerCase();

    if (
        value ===
        "safe"
    ) {

        return "Safe";

    }

    if (
        value ===
        "target"
    ) {

        return "Target";

    }

    if (
        value ===
        "reach"
    ) {

        return "Reach";

    }

    return null;

}

resultFilterButtons.forEach(
    button => {

        button.addEventListener(
            "click",
            () => {

                activeResultFilter =
                    button.dataset
                        .resultFilter;

                updateResultFilterButtons(
                    activeResultFilter
                );

                if (
                    latestPredictionData
                ) {

                    renderResults(
                        latestPredictionData
                    );

                }

            }
        );

    }
);

function updateResultFilterButtons(
    filter
) {

    resultFilterButtons.forEach(
        button => {

            button.classList.toggle(
                "active",
                button.dataset
                    .resultFilter ===
                    filter
            );

        }
    );

}

/* =========================================================
   RESULT CARD
========================================================= */

function createResultCard(
    result
) {

    const card =
        document.createElement(
            "article"
        );

    card.className =
        "result-card";

    const probabilityValue =
        result.estimated_probability;

    let probabilityText =
        "—";

    if (
        probabilityValue !==
            null &&
        probabilityValue !==
            undefined &&
        Number.isFinite(
            Number(
                probabilityValue
            )
        )
    ) {

        probabilityText =
            `${Number(
                probabilityValue
            ).toFixed(
                1
            )}%`;

    }

    const tier =
        normalizeTier(
            result.tier
        ) ||
        "Target";

    const tierClass =
        tier.toLowerCase();

    const reasoning =
        result.probability_reasoning ||
        "Historical scoring explanation is not available.";

    const historicalFit =
        result.historical_fit_score ??
        "—";

    const latestCutoff =
        result.latest_cutoff ??
        "—";

    const latestRank =
        result.latest_closing_rank ??
        "—";

    const years =
        result.available_years ??
        "—";

    const mode =
        latestPredictionData?.mode ||
        "cutoff";

    const changeValue =
        mode ===
        "cutoff"
            ? result.cutoff_change
            : result.rank_change;

    let changeText =
        "—";

    if (
        changeValue !==
            null &&
        changeValue !==
            undefined
    ) {

        changeText =
            `${
                Number(
                    changeValue
                ) > 0
                    ? "+"
                    : ""
            }${
                changeValue
            }`;

    }

    const instTier =
        result.institutional_tier;

    let instTierBadge = "";
    if (instTier === "Tier-1") {
        instTierBadge = `<span class="tier-inst-badge tier-inst-1" title="Premier Government / Top Autonomous Institution">🏛️ Tier-1</span>`;
    } else if (instTier === "Tier-2") {
        instTierBadge = `<span class="tier-inst-badge tier-inst-2" title="Established Engineering College">🏢 Tier-2</span>`;
    } else if (instTier === "Tier-3") {
        instTierBadge = `<span class="tier-inst-badge tier-inst-3" title="Developing / Regional Engineering College">🏫 Tier-3</span>`;
    }

    card.innerHTML = `

        <div class="result-card-header">

            <div>

                <div class="result-college-name">

                    ${escapeHtml(
                        result.college_name ||
                        "Unknown College"
                    )}
                    ${instTierBadge}

                </div>

                <div class="result-branch">

                    ${escapeHtml(
                        result.branch_name ||
                        result.branch_code ||
                        "Unknown Branch"
                    )}

                </div>

                <div class="result-location">

                    ${escapeHtml(
                        result.district ||
                        "Unknown District"
                    )}

                </div>

            </div>

            <div class="result-probability-block">

                <div
                    class="
                        result-probability
                        ${tierClass}
                    "
                >

                    ${escapeHtml(
                        probabilityText
                    )}

                </div>

                <div
                    class="
                        tier-badge
                        tier-${tierClass}
                    "
                >

                    ${tierEmoji(
                        tier
                    )}

                    ${escapeHtml(
                        tier
                    )}

                </div>

            </div>

        </div>

        <div class="result-stats">

            <div class="result-stat">

                <span class="result-stat-label">
                    Historical Fit
                </span>

                <span class="result-stat-value">

                    ${escapeHtml(
                        String(
                            historicalFit
                        )
                    )}%

                </span>

            </div>

            <div class="result-stat">

                <span class="result-stat-label">
                    Latest Cutoff
                </span>

                <span class="result-stat-value">

                    ${escapeHtml(
                        String(
                            latestCutoff
                        )
                    )}

                </span>

            </div>

            <div class="result-stat">

                <span class="result-stat-label">
                    Latest Closing Rank
                </span>

                <span class="result-stat-value">

                    ${escapeHtml(
                        String(
                            latestRank
                        )
                    )}

                </span>

            </div>

            <div class="result-stat">

                <span class="result-stat-label">
                    Historical Years
                </span>

                <span class="result-stat-value">

                    ${escapeHtml(
                        String(
                            years
                        )
                    )}

                </span>

            </div>

            <div class="result-stat">

                <span class="result-stat-label">
                    5-Year Change
                </span>

                <span class="result-stat-value">

                    ${escapeHtml(
                        String(
                            changeText
                        )
                    )}

                </span>

            </div>

        </div>

        <details class="result-reasoning">

            <summary>
                Why this estimate?
            </summary>

            <div class="result-reasoning-text">

                ${escapeHtml(
                    reasoning
                )}

            </div>

        </details>

        <div class="result-actions">

            <button
                class="add-choice-btn"
                type="button"
            >
                Add to Choice Optimizer
            </button>

            <button
                class="view-trend-btn"
                type="button"
                title="View 5-year historical cutoff trajectory"
            >
                📈 5-Yr Trend
            </button>

            <button
                class="branch-swap-btn"
                type="button"
                title="Discover other engineering branches in this campus"
            >
                🔄 Campus Branches
            </button>

        </div>

    `;

    const addButton =
        card.querySelector(
            ".add-choice-btn"
        );

    const alreadyAdded =
        choices.some(
            choice =>

                String(
                    choice.college_code
                ) ===
                    String(
                        result.college_code
                    ) &&

                String(
                    choice.branch_code
                ) ===
                    String(
                        result.branch_code
                    )
        );

    if (
        alreadyAdded
    ) {

        addButton.textContent =
            "Already Added";

        addButton.disabled =
            true;

    }

    addButton.addEventListener(
        "click",
        () => {

            const added =
                addChoice(
                    result
                );

            addButton.textContent =
                added
                    ? "Added to Choices"
                    : "Already Added";

            addButton.disabled =
                true;

        }
    );

    const viewTrendBtn = card.querySelector(".view-trend-btn");
    if (viewTrendBtn) {
        viewTrendBtn.addEventListener("click", () => {
            openTrendModal(result);
        });
    }

    const branchSwapBtn = card.querySelector(".branch-swap-btn");
    if (branchSwapBtn) {
        branchSwapBtn.addEventListener("click", () => {
            openBranchSwapModal(result);
        });
    }

    return card;

}

function tierEmoji(
    tier
) {

    if (
        tier ===
        "Safe"
    ) {

        return "🛡";

    }

    if (
        tier ===
        "Reach"
    ) {

        return "🔥";

    }

    return "🎯";

}

/* =========================================================
   RAG
========================================================= */

async function loadRagExplanation(
    mode,
    input
) {

    ragSection.classList.remove(
        "hidden"
    );

    ragLoading.classList.remove(
        "hidden"
    );

    ragContent.innerHTML =
        "";

    hideRagError();

    const endpoint =
        mode ===
        "cutoff"
            ? "/api/rag-explanation"
            : "/api/rank-rag-explanation";

    const params =
        new URLSearchParams();

    if (
        mode ===
        "cutoff"
    ) {

        params.set(
            "cutoff_mark",
            input.cutoffMark
        );

    } else {

        params.set(
            "state_rank",
            input.stateRank
        );

    }

    params.set(
        "community",
        input.community
    );

    if (
        input.districts.length ===
        1
    ) {

        params.set(
            "district",
            input.districts[0]
        );

    }

    if (
        input.branches.length ===
        1
    ) {

        params.set(
            "branch_code",
            input.branches[0]
        );

    }

    if (
        input.collegeCode
    ) {

        params.set(
            "college_code",
            input.collegeCode
        );

    }

    try {

        const response =
            await fetch(
                `${endpoint}?${params.toString()}`
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            data.status !== "ok"
        ) {

            throw new Error(
                data.message ||
                "RAG explanation failed."
            );

        }

        ragModelBadge.textContent =
            data.generation_model ||
            "Gemini";

        renderRag(
            data.explanation ||
            "No explanation was returned."
        );

        if (
            input.districts.length >
                1 ||
            input.branches.length >
                1
        ) {

            ragSubtitle.textContent =
                "Gemini explanation based on the selected filters and available historical evidence.";

        } else {

            ragSubtitle.textContent =
                "Gemini explanation grounded in historical TNEA evidence.";

        }

    } catch (
        error
    ) {

        showRagError(
            "AI historical analysis could not be generated right now. " +
            error.message
        );

    } finally {

        ragLoading.classList.add(
            "hidden"
        );

    }

}

function renderRag(
    text
) {

    const sections = {

        Summary:
            [],

        "Historical Evidence":
            [],

        "How to Interpret":
            [],

        Limitations:
            []

    };

    let currentSection =
        "Summary";

    String(
        text
    )
        .split(
            "\n"
        )
        .forEach(
            line => {

                const cleaned =
                    line
                        .replace(
                            /\*\*/g,
                            ""
                        )
                        .trim();

                if (
                    !cleaned
                ) {

                    return;

                }

                const heading =
                    cleaned.replace(
                        /:$/,
                        ""
                    );

                if (
                    Object.prototype.hasOwnProperty.call(
                        sections,
                        heading
                    )
                ) {

                    currentSection =
                        heading;

                    return;

                }

                sections[
                    currentSection
                ].push(
                    cleaned
                );

            }
        );

    ragContent.innerHTML =
        "";

    Object.entries(
        sections
    ).forEach(
        (
            [
                heading,
                paragraphs
            ]
        ) => {

            if (
                paragraphs.length ===
                0
            ) {

                return;

            }

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "rag-card";

            const title =
                document.createElement(
                    "h3"
                );

            title.textContent =
                heading;

            card.appendChild(
                title
            );

            paragraphs.forEach(
                paragraph => {

                    const p =
                        document.createElement(
                            "p"
                        );

                    p.textContent =
                        paragraph;

                    card.appendChild(
                        p
                    );

                }
            );

            ragContent.appendChild(
                card
            );

        }
    );

    if (
        ragContent.children.length ===
        0
    ) {

        const card =
            document.createElement(
                "div"
            );

        card.className =
            "rag-card";

        const p =
            document.createElement(
                "p"
            );

        p.textContent =
            String(
                text
            );

        card.appendChild(
            p
        );

        ragContent.appendChild(
            card
        );

    }

}

/* =========================================================
   CHOICE OPTIMIZER
========================================================= */

/*
   TWO SECTIONS:

   1. AI SUGGESTED CHOICE LIST
      Automatically generated from the latest prediction
      probabilities and historical signals.

      Student can:
      - Move up
      - Move down
      - Drag
      - Remove
      - Add individual choices to My Choice List
      - Use the complete list

   2. MY CHOICE LIST
      Completely controlled by the student.

      The system NEVER automatically reorders this list.
*/

function createOptimizerControls() {

    if (
        !optimizerTab
    ) {

        return;

    }

    const panel =
        optimizerTab.querySelector(
            ".page-panel"
        );

    if (
        !panel
    ) {

        return;

    }

    if (
        byId(
            "optimizerControls"
        )
    ) {

        return;

    }

    const header =
        panel.querySelector(
            ".section-header"
        );

    if (
        header
    ) {

        const heading =
            header.querySelector(
                "h2"
            );

        const description =
            header.querySelector(
                "p"
            );

        if (
            heading
        ) {

            heading.textContent =
                "Build Your Choice List";

        }

        if (
            description
        ) {

            description.textContent =
                "Start with an AI-suggested list or build your own. You control the final preference order.";

        }

    }

    const controls =
        document.createElement(
            "div"
        );

    controls.id =
        "optimizerControls";

    controls.innerHTML = `

        <section
            style="
                margin-top:18px;
                padding:18px;
                border:1px solid rgba(99,102,241,0.20);
                border-radius:16px;
                background:linear-gradient(
                    135deg,
                    rgba(99,102,241,0.09),
                    rgba(6,182,212,0.04)
                );
            "
        >

            <div
                style="
                    display:flex;
                    justify-content:space-between;
                    align-items:flex-start;
                    gap:16px;
                    flex-wrap:wrap;
                "
            >

                <div>

                    <div
                        style="
                            color:#818cf8;
                            font-size:0.68rem;
                            font-weight:900;
                            letter-spacing:0.08em;
                        "
                    >
                        AI ASSISTED
                    </div>

                    <div
                        style="
                            color:#f8fafc;
                            font-size:1rem;
                            font-weight:900;
                            margin-top:3px;
                        "
                    >
                        AI Suggested Choice List
                    </div>

                    <div
                        style="
                            color:#94a3b8;
                            font-size:0.74rem;
                            line-height:1.5;
                            margin-top:5px;
                            max-width:780px;
                        "
                    >
                        Automatically generated from your latest prediction probabilities, historical fit and Safe / Target / Reach classification. You can edit it completely.
                    </div>

                </div>

                <div
                    style="
                        display:flex;
                        gap:8px;
                        flex-wrap:wrap;
                    "
                >

                    <button
                        id="regenerateAIButton"
                        type="button"
                        class="secondary-button"
                    >
                        Regenerate
                    </button>

                    <button
                        id="useAIListButton"
                        type="button"
                        class="primary-button"
                    >
                        Use This List
                    </button>

                </div>

            </div>

            <div
                id="aiSuggestedSummary"
                style="
                    margin-top:12px;
                    color:#cbd5e1;
                    font-size:0.73rem;
                    line-height:1.5;
                "
            ></div>

            <div
                id="aiSuggestedList"
                style="
                    display:flex;
                    flex-direction:column;
                    gap:9px;
                    margin-top:12px;
                "
            ></div>

            <div
                id="aiSuggestedEmpty"
                style="
                    display:none;
                    padding:18px;
                    margin-top:12px;
                    border-radius:12px;
                    border:1px dashed rgba(148,163,184,0.18);
                    color:#64748b;
                    font-size:0.75rem;
                    line-height:1.5;
                "
            >
                Run a prediction first to generate the AI-suggested list.
            </div>

        </section>

        <section
            style="
                margin-top:18px;
                margin-bottom:10px;
            "
        >

            <div
                style="
                    color:#818cf8;
                    font-size:0.68rem;
                    font-weight:900;
                    letter-spacing:0.08em;
                "
            >
                YOUR PREFERENCES
            </div>

            <div
                style="
                    color:#f8fafc;
                    font-size:1rem;
                    font-weight:900;
                    margin-top:3px;
                "
            >
                My Choice List
            </div>

            <div
                style="
                    color:#94a3b8;
                    font-size:0.74rem;
                    line-height:1.5;
                    margin-top:5px;
                "
            >
                Your final choice order. The application never automatically reorders this list.
            </div>

            <div
                id="optimizerListSummary"
                style="
                    margin-top:10px;
                "
            ></div>

        </section>

        <div
            style="
                margin-top:10px;
                padding:10px 12px;
                border-radius:10px;
                background:rgba(148,163,184,0.035);
                border:1px solid rgba(148,163,184,0.08);
                color:#64748b;
                font-size:0.7rem;
                line-height:1.5;
            "
        >
            Drag choices to reorder them or use ↑ / ↓. Probability and tier are supporting information only.
        </div>

    `;

    const empty =
        byId(
            "emptyChoices"
        );

    if (
        empty
    ) {

        panel.insertBefore(
            controls,
            empty
        );

    } else {

        panel.appendChild(
            controls
        );

    }

    byId(
        "regenerateAIButton"
    )?.addEventListener(
        "click",
        () => {

            generateAISuggestedList();

        }
    );

    byId(
        "useAIListButton"
    )?.addEventListener(
        "click",
        () => {

            useAISuggestedList();

        }
    );

    renderAISuggestedList();

}

/* =========================================================
   AI SUGGESTED LIST GENERATION
========================================================= */

async function generateAISuggestedList() {

    if (
        !Array.isArray(
            latestResults
        ) ||
        latestResults.length ===
        0
    ) {

        aiSuggestedChoices =
            [];

        renderAISuggestedList();

        return;

    }

    try {
        const optResponse = await fetch("/api/choices/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ candidates: latestResults })
        });
        const optData = await optResponse.json();
        if (optData.status === "ok" && Array.isArray(optData.optimized_choices) && optData.optimized_choices.length > 0) {
            aiSuggestedChoices = optData.optimized_choices.map(normalizeChoice);
            renderAISuggestedList();
            return;
        }
    } catch (optErr) {
        // Fall through to local heuristic
    }


    const validResults =
        latestResults
            .map(
                normalizeChoice
            )
            .filter(
                result =>
                    Number.isFinite(
                        Number(
                            result.estimated_probability
                        )
                    )
            );

    if (
        validResults.length ===
        0
    ) {

        aiSuggestedChoices =
            [];

        renderAISuggestedList();

        return;

    }

    const sorted =
        [
            ...validResults
        ].sort(
            compareProbabilityDescending
        );

    const safe =
        sorted.filter(
            item =>
                normalizeTier(
                    item.tier
                ) ===
                "Safe"
        );

    const target =
        sorted.filter(
            item =>
                normalizeTier(
                    item.tier
                ) ===
                "Target"
        );

    const reach =
        sorted.filter(
            item =>
                normalizeTier(
                    item.tier
                ) ===
                "Reach"
        );

    const selected =
        [];

    const selectedKeys =
        new Set();

    function addCandidate(
        candidate
    ) {

        if (
            !candidate ||
            selected.length >=
            12
        ) {

            return;

        }

        const key =
            choiceKey(
                candidate
            );

        if (
            selectedKeys.has(
                key
            )
        ) {

            return;

        }

        selected.push(
            candidate
        );

        selectedKeys.add(
            key
        );

    }

    /*
       First include up to four choices
       from each available tier.
    */

    safe
        .slice(
            0,
            4
        )
        .forEach(
            addCandidate
        );

    target
        .slice(
            0,
            4
        )
        .forEach(
            addCandidate
        );

    reach
        .slice(
            0,
            4
        )
        .forEach(
            addCandidate
        );

    /*
       Fill any remaining slots using
       highest probability options.
    */

    sorted.forEach(
        candidate => {

            if (
                selected.length >=
                12
            ) {

                return;

            }

            addCandidate(
                candidate
            );

        }
    );

    /*
       Initial AI order is probability based.
       The student can freely change this afterwards.
    */

    selected.sort(
        compareProbabilityDescending
    );

    aiSuggestedChoices =
        selected;

    renderAISuggestedList();

}

/* =========================================================
   AI LIST RENDER
========================================================= */

function renderAISuggestedList() {

    const container =
        byId(
            "aiSuggestedList"
        );

    const summary =
        byId(
            "aiSuggestedSummary"
        );

    const empty =
        byId(
            "aiSuggestedEmpty"
        );

    if (
        !container ||
        !summary ||
        !empty
    ) {

        return;

    }

    container.innerHTML =
        "";

    if (
        aiSuggestedChoices.length ===
        0
    ) {

        summary.textContent =
            "No AI suggestion is available yet.";

        empty.style.display =
            "block";

        return;

    }

    empty.style.display =
        "none";

    const counts =
        calculateTierCountsForList(
            aiSuggestedChoices
        );

    summary.textContent =
        `Generated ${
            aiSuggestedChoices.length
        } starting choices · ${
            counts.Safe
        } Safe · ${
            counts.Target
        } Target · ${
            counts.Reach
        } Reach`;

    aiSuggestedChoices.forEach(
        (
            choice,
            index
        ) => {

            container.appendChild(
                createAISuggestedCard(
                    choice,
                    index
                )
            );

        }
    );

}

/* =========================================================
   AI CARD
========================================================= */

function createAISuggestedCard(
    choice,
    index
) {

    const card =
        document.createElement(
            "div"
        );

    card.draggable =
        true;

    const isLight = document.documentElement.getAttribute("data-theme") === "light";

    card.className = "ai-suggested-card";

    card.style.cssText = `
        display:grid;
        grid-template-columns:42px minmax(0,1fr) auto;
        gap:12px;
        align-items:center;
        padding:12px;
        border-radius:13px;
        border:1px solid ${isLight ? '#e2e8f0' : 'rgba(148,163,184,0.12)'};
        background:${isLight ? '#ffffff' : 'rgba(18,26,43,0.66)'};
    `;

    const tier =
        normalizeTier(
            choice.tier
        ) ||
        "Target";

    const probability =
        formatProbability(
            choice.estimated_probability
        );

    const fit =
        choice.historical_fit_score ??
        "—";

    const tierColor =
        getTierColor(
            tier
        );

    const numBg = isLight ? "rgba(99,102,241,0.08)" : "rgba(99,102,241,0.12)";
    const numBorder = isLight ? "rgba(99,102,241,0.25)" : "rgba(99,102,241,0.22)";
    const numColor = isLight ? "#4f46e5" : "#c7d2fe";
    const titleColor = isLight ? "#0f172a" : "#f8fafc";
    const branchColor = isLight ? "#4f46e5" : "#a5b4fc";
    const pillBorder = isLight ? "#cbd5e1" : "rgba(148,163,184,0.14)";
    const pillBg = isLight ? "#f1f5f9" : "rgba(148,163,184,0.04)";
    const pillColor = isLight ? "#334155" : "#cbd5e1";
    const pillFitColor = isLight ? "#475569" : "#94a3b8";

    card.innerHTML = `

        <div
            style="
                width:36px;
                height:36px;
                border-radius:10px;
                display:flex;
                align-items:center;
                justify-content:center;
                background:${numBg};
                border:1px solid ${numBorder};
                color:${numColor};
                font-family:var(--font-mono, monospace);
                font-weight:900;
                font-size:0.76rem;
                cursor:grab;
            "
            title="Drag to reorder"
        >

            ☰

            <span
                style="
                    margin-left:4px;
                "
            >
                ${index + 1}
            </span>

        </div>

        <div>

            <div
                style="
                    color:${titleColor};
                    font-size:0.84rem;
                    font-weight:900;
                    line-height:1.35;
                "
            >

                ${escapeHtml(
                    choice.college_name ||
                    "Unknown College"
                )}

            </div>

            <div
                style="
                    color:${branchColor};
                    font-size:0.76rem;
                    font-weight:700;
                    margin-top:3px;
                "
            >

                ${escapeHtml(
                    choice.branch_name ||
                    choice.branch_code ||
                    "Unknown Branch"
                )}

            </div>

            <div
                style="
                    display:flex;
                    flex-wrap:wrap;
                    gap:6px;
                    margin-top:7px;
                "
            >

                <span
                    style="
                        font-size:0.66rem;
                        padding:3px 7px;
                        border-radius:999px;
                        border:1px solid ${tierColor.border};
                        background:${tierColor.background};
                        color:${tierColor.text};
                        font-weight:900;
                    "
                >

                    ${tierEmoji(
                        tier
                    )}

                    ${escapeHtml(
                        tier
                    )}

                </span>

                <span
                    style="
                        font-size:0.66rem;
                        padding:3px 7px;
                        border-radius:999px;
                        border:1px solid ${pillBorder};
                        background:${pillBg};
                        color:${pillColor};
                        font-weight:800;
                    "
                >

                    Chance:
                    ${escapeHtml(
                        probability
                    )}

                </span>

                <span
                    style="
                        font-size:0.66rem;
                        padding:3px 7px;
                        border-radius:999px;
                        border:1px solid ${pillBorder};
                        background:${pillBg};
                        color:${pillFitColor};
                        font-weight:800;
                    "
                >

                    Fit:
                    ${escapeHtml(
                        String(
                            fit
                        )
                    )}%

                </span>

                <span
                    style="
                        font-size:0.66rem;
                        padding:3px 7px;
                        border-radius:999px;
                        border:1px solid ${pillBorder};
                        background:${pillBg};
                        color:${pillFitColor};
                        font-weight:800;
                    "
                >

                    ${escapeHtml(
                        choice.district ||
                        "Unknown District"
                    )}

                </span>

            </div>

        </div>

        <div
            style="
                display:flex;
                flex-wrap:wrap;
                justify-content:flex-end;
                gap:5px;
            "
        >

            <button
                class="ai-move-up"
                type="button"
                ${
                    index ===
                    0
                        ? "disabled"
                        : ""
                }
            >
                ↑
            </button>

            <button
                class="ai-move-down"
                type="button"
                ${
                    index ===
                    aiSuggestedChoices.length - 1
                        ? "disabled"
                        : ""
                }
            >
                ↓
            </button>

            <button
                class="ai-add-my-list"
                type="button"
            >
                Add
            </button>

            <button
                class="ai-remove"
                type="button"
            >
                Remove
            </button>

        </div>

    `;

    const buttons =
        [
            card.querySelector(
                ".ai-move-up"
            ),

            card.querySelector(
                ".ai-move-down"
            ),

            card.querySelector(
                ".ai-add-my-list"
            ),

            card.querySelector(
                ".ai-remove"
            )
        ];

    buttons.forEach(
        button => {

            if (
                !button
            ) {

                return;

            }

            button.style.cssText = `
                min-height:31px;
                padding:0 8px;
                border-radius:8px;
                border:1px solid rgba(148,163,184,0.14);
                background:rgba(15,23,42,0.68);
                color:#cbd5e1;
                cursor:pointer;
                font-size:0.68rem;
                font-weight:900;
            `;

        }
    );

    card.querySelector(
        ".ai-move-up"
    )?.addEventListener(
        "click",
        () => {

            moveAISuggestedChoice(
                index,
                -1
            );

        }
    );

    card.querySelector(
        ".ai-move-down"
    )?.addEventListener(
        "click",
        () => {

            moveAISuggestedChoice(
                index,
                1
            );

        }
    );

    card.querySelector(
        ".ai-add-my-list"
    )?.addEventListener(
        "click",
        event => {

            const button =
                event.currentTarget;

            const added =
                addChoice(
                    choice
                );

            button.textContent =
                added
                    ? "Added"
                    : "Already Added";

            button.disabled =
                true;

        }
    );

    card.querySelector(
        ".ai-remove"
    )?.addEventListener(
        "click",
        () => {

            removeAISuggestedChoice(
                index
            );

        }
    );

    card.addEventListener(
        "dragstart",
        event => {

            draggedAIChoiceIndex =
                index;

            card.style.opacity =
                "0.45";

            event.dataTransfer.effectAllowed =
                "move";

            event.dataTransfer.setData(
                "text/plain",
                String(
                    index
                )
            );

        }
    );

    card.addEventListener(
        "dragend",
        () => {

            draggedAIChoiceIndex =
                null;

            card.style.opacity =
                "1";

        }
    );

    card.addEventListener(
        "dragover",
        event => {

            event.preventDefault();

            event.dataTransfer.dropEffect =
                "move";

        }
    );

    card.addEventListener(
        "drop",
        event => {

            event.preventDefault();

            let sourceIndex =
                draggedAIChoiceIndex;

            if (
                sourceIndex ===
                null
            ) {

                sourceIndex =
                    Number(
                        event.dataTransfer.getData(
                            "text/plain"
                        )
                    );

            }

            if (
                !Number.isInteger(
                    sourceIndex
                ) ||
                sourceIndex < 0 ||
                sourceIndex >=
                    aiSuggestedChoices.length
            ) {

                return;

            }

            if (
                sourceIndex ===
                index
            ) {

                return;

            }

            const moved =
                aiSuggestedChoices.splice(
                    sourceIndex,
                    1
                )[0];

            aiSuggestedChoices.splice(
                index,
                0,
                moved
            );

            draggedAIChoiceIndex =
                null;

            renderAISuggestedList();

        }
    );

    return card;

}

/* =========================================================
   MOVE AI CHOICE
========================================================= */

function moveAISuggestedChoice(
    index,
    direction
) {

    const newIndex =
        index +
        direction;

    if (
        newIndex < 0 ||
        newIndex >=
            aiSuggestedChoices.length
    ) {

        return;

    }

    const temp =
        aiSuggestedChoices[
            index
        ];

    aiSuggestedChoices[
        index
    ] =
        aiSuggestedChoices[
            newIndex
        ];

    aiSuggestedChoices[
        newIndex
    ] =
        temp;

    renderAISuggestedList();

}

/* =========================================================
   REMOVE AI CHOICE
========================================================= */

function removeAISuggestedChoice(
    index
) {

    if (
        index < 0 ||
        index >=
            aiSuggestedChoices.length
    ) {

        return;

    }

    aiSuggestedChoices.splice(
        index,
        1
    );

    renderAISuggestedList();

}

/* =========================================================
   USE AI LIST
========================================================= */

function useAISuggestedList() {

    if (
        aiSuggestedChoices.length ===
        0
    ) {

        alert(
            "Run a prediction first to generate the AI-suggested choice list."
        );

        return;

    }

    /*
       Copy the CURRENT edited AI list into My Choice List.

       This preserves the exact order that the student
       created inside the AI section.
    */

    choices =
        aiSuggestedChoices.map(
            normalizeChoice
        );

    saveChoices();

    renderChoices();

    alert(
        "The AI-suggested list has been copied to My Choice List in the same order. You can now edit it freely."
    );

}

/* =========================================================
   ADD TO MY LIST
========================================================= */

function addChoice(
    choice
) {

    const normalized =
        normalizeChoice(
            choice
        );

    const alreadyExists =
        choices.some(
            item =>

                String(
                    item.college_code
                ) ===
                    String(
                        normalized.college_code
                    ) &&

                String(
                    item.branch_code
                ) ===
                    String(
                        normalized.branch_code
                    )
        );

    if (
        alreadyExists
    ) {

        return false;

    }

    choices.push(
        normalized
    );

    saveChoices();

    renderChoices();

    return true;

}

/* =========================================================
   NORMALIZE CHOICE
========================================================= */

function normalizeChoice(
    choice
) {

    return {

        college_code:
            choice.college_code ??
            "",

        college_name:
            choice.college_name ??
            "",

        branch_code:
            choice.branch_code ??
            "",

        branch_name:
            choice.branch_name ??
            "",

        district:
            choice.district ??
            "",

        latest_cutoff:
            choice.latest_cutoff ??
            null,

        latest_closing_rank:
            choice.latest_closing_rank ??
            null,

        historical_fit_score:
            choice.historical_fit_score ??
            null,

        estimated_probability:
            choice.estimated_probability ??
            null,

        tier:
            normalizeTier(
                choice.tier
            ),

        probability_reasoning:
            choice.probability_reasoning ??
            ""

    };

}

/* =========================================================
   REMOVE MY CHOICE
========================================================= */

function removeChoice(
    index
) {

    if (
        index < 0 ||
        index >=
            choices.length
    ) {

        return;

    }

    choices.splice(
        index,
        1
    );

    saveChoices();

    renderChoices();

}

/* =========================================================
   MOVE MY CHOICE UP
========================================================= */

function moveChoiceUp(
    index
) {

    if (
        index <=
        0
    ) {

        return;

    }

    const previous =
        choices[
            index - 1
        ];

    choices[
        index - 1
    ] =
        choices[
            index
        ];

    choices[
        index
    ] =
        previous;

    saveChoices();

    renderChoices();

}

/* =========================================================
   MOVE MY CHOICE DOWN
========================================================= */

function moveChoiceDown(
    index
) {

    if (
        index < 0 ||
        index >=
            choices.length - 1
    ) {

        return;

    }

    const next =
        choices[
            index + 1
        ];

    choices[
        index + 1
    ] =
        choices[
            index
        ];

    choices[
        index
    ] =
        next;

    saveChoices();

    renderChoices();

}

/* =========================================================
   MY CHOICE DRAG START
========================================================= */

function handleChoiceDragStart(
    event,
    index
) {

    draggedChoiceIndex =
        index;

    event.dataTransfer.effectAllowed =
        "move";

    event.dataTransfer.setData(
        "text/plain",
        String(
            index
        )
    );

    event.currentTarget.style.opacity =
        "0.45";

}

/* =========================================================
   MY CHOICE DRAG END
========================================================= */

function handleChoiceDragEnd(
    event
) {

    event.currentTarget.style.opacity =
        "1";

    draggedChoiceIndex =
        null;

}

/* =========================================================
   MY CHOICE DRAG OVER
========================================================= */

function handleChoiceDragOver(
    event
) {

    event.preventDefault();

    event.dataTransfer.dropEffect =
        "move";

}

/* =========================================================
   MY CHOICE DROP
========================================================= */

function handleChoiceDrop(
    event,
    targetIndex
) {

    event.preventDefault();

    let sourceIndex =
        draggedChoiceIndex;

    if (
        sourceIndex ===
        null
    ) {

        sourceIndex =
            Number(
                event.dataTransfer.getData(
                    "text/plain"
                )
            );

    }

    if (
        !Number.isInteger(
            sourceIndex
        ) ||
        sourceIndex < 0 ||
        sourceIndex >=
            choices.length
    ) {

        draggedChoiceIndex =
            null;

        return;

    }

    if (
        sourceIndex ===
        targetIndex
    ) {

        draggedChoiceIndex =
            null;

        return;

    }

    const moved =
        choices.splice(
            sourceIndex,
            1
        )[0];

    choices.splice(
        targetIndex,
        0,
        moved
    );

    draggedChoiceIndex =
        null;

    saveChoices();

    renderChoices();

}

/* =========================================================
   RENDER MY CHOICE LIST
========================================================= */

function renderChoices() {

    if (
        !choicesContainer ||
        !emptyChoices
    ) {

        return;

    }

    if (
        choices.length ===
        0
    ) {

        emptyChoices.classList.remove(
            "hidden"
        );

        choicesContainer.classList.add(
            "hidden"
        );

        updateOptimizerListSummary();

        return;

    }

    emptyChoices.classList.add(
        "hidden"
    );

    choicesContainer.classList.remove(
        "hidden"
    );

    choicesContainer.innerHTML =
        "";

    choices.forEach(
        (
            choice,
            index
        ) => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "choice-card";

            card.draggable =
                true;

            const probability =
                formatProbability(
                    choice.estimated_probability
                );

            const tier =
                normalizeTier(
                    choice.tier
                );

            const tierLabel =
                tier ||
                "—";

            const tierColor =
                getTierColor(
                    tier
                );

            card.innerHTML = `

                <div
                    class="choice-number"
                    style="
                        cursor:grab;
                    "
                    title="Drag to reorder"
                >

                    ☰

                    <span
                        style="
                            margin-left:5px;
                        "
                    >
                        ${index + 1}
                    </span>

                </div>

                <div>

                    <div class="choice-college">

                        ${escapeHtml(
                            choice.college_name
                        )}

                    </div>

                    <div class="choice-branch">

                        ${escapeHtml(
                            choice.branch_name ||
                            choice.branch_code
                        )}

                    </div>

                    <div class="choice-meta">

                        ${escapeHtml(
                            choice.district ||
                            "Unknown District"
                        )}

                        · Code:

                        ${escapeHtml(
                            String(
                                choice.college_code
                            )
                        )}

                    </div>

                    <div
                        style="
                            display:flex;
                            gap:8px;
                            flex-wrap:wrap;
                            margin-top:7px;
                        "
                    >

                        <span
                            style="
                                font-size:0.67rem;
                                padding:4px 8px;
                                border-radius:999px;
                                border:1px solid ${tierColor.border};
                                background:${tierColor.background};
                                color:${tierColor.text};
                                font-weight:900;
                            "
                        >

                            ${tierEmoji(
                                tier
                            )}

                            ${escapeHtml(
                                tierLabel
                            )}

                        </span>

                        <span
                            style="
                                font-size:0.67rem;
                                padding:4px 8px;
                                border-radius:999px;
                                border:1px solid rgba(148,163,184,0.16);
                                background:rgba(148,163,184,0.05);
                                color:#cbd5e1;
                                font-weight:800;
                            "
                        >

                            Chance:
                            ${escapeHtml(
                                probability
                            )}

                        </span>

                    </div>

                </div>

                <div class="choice-stats">

                    <div>

                        Cutoff:
                        ${escapeHtml(
                            String(
                                choice.latest_cutoff ??
                                "—"
                            )
                        )}

                    </div>

                    <div>

                        Rank:
                        ${escapeHtml(
                            String(
                                choice.latest_closing_rank ??
                                "—"
                            )
                        )}

                    </div>

                </div>

                <div
                    style="
                        display:flex;
                        gap:6px;
                        align-items:center;
                        flex-wrap:wrap;
                    "
                >

                    <button
                        class="optimizer-move-up"
                        type="button"
                        title="Move up"
                        ${
                            index ===
                            0
                                ? "disabled"
                                : ""
                        }
                    >
                        ↑
                    </button>

                    <button
                        class="optimizer-move-down"
                        type="button"
                        title="Move down"
                        ${
                            index ===
                            choices.length - 1
                                ? "disabled"
                                : ""
                        }
                    >
                        ↓
                    </button>

                    <button
                        class="remove-choice-btn"
                        type="button"
                    >
                        Remove
                    </button>

                </div>

            `;

            card.addEventListener(
                "dragstart",
                event => {

                    handleChoiceDragStart(
                        event,
                        index
                    );

                }
            );

            card.addEventListener(
                "dragend",
                handleChoiceDragEnd
            );

            card.addEventListener(
                "dragover",
                handleChoiceDragOver
            );

            card.addEventListener(
                "drop",
                event => {

                    handleChoiceDrop(
                        event,
                        index
                    );

                }
            );

            card
                .querySelector(
                    ".optimizer-move-up"
                )
                ?.addEventListener(
                    "click",
                    () => {

                        moveChoiceUp(
                            index
                        );

                    }
                );

            card
                .querySelector(
                    ".optimizer-move-down"
                )
                ?.addEventListener(
                    "click",
                    () => {

                        moveChoiceDown(
                            index
                        );

                    }
                );

            card
                .querySelector(
                    ".remove-choice-btn"
                )
                ?.addEventListener(
                    "click",
                    () => {

                        removeChoice(
                            index
                        );

                    }
                );

            choicesContainer.appendChild(
                card
            );

        }
    );

    updateOptimizerListSummary();

}

/* =========================================================
   MY LIST SUMMARY
========================================================= */

function updateOptimizerListSummary() {

    const summary =
        byId(
            "optimizerListSummary"
        );

    if (
        !summary
    ) {

        return;

    }

    const counts =
        calculateTierCountsForList(
            choices
        );

    if (
        choices.length ===
        0
    ) {

        summary.innerHTML = `
            <div
                style="
                    color:#64748b;
                    font-size:0.72rem;
                "
            >
                No choices added yet.
            </div>
        `;

        return;

    }

    summary.innerHTML = `

        <div
            style="
                display:flex;
                gap:8px;
                flex-wrap:wrap;
            "
        >

            <span class="
                distribution-pill
                distribution-safe
            ">
                🛡 Safe:
                ${counts.Safe}
            </span>

            <span class="
                distribution-pill
                distribution-target
            ">
                🎯 Target:
                ${counts.Target}
            </span>

            <span class="
                distribution-pill
                distribution-reach
            ">
                🔥 Reach:
                ${counts.Reach}
            </span>

            <span
                class="distribution-pill"
                style="
                    background:rgba(148,163,184,0.06);
                    color:#94a3b8;
                    border:1px solid rgba(148,163,184,0.15);
                "
            >
                Total:
                ${choices.length}
            </span>

        </div>

    `;

}

/* =========================================================
   TIER COUNTS
========================================================= */

function calculateTierCountsForList(
    list
) {

    const counts = {

        Safe:
            0,

        Target:
            0,

        Reach:
            0

    };

    list.forEach(
        choice => {

            const tier =
                normalizeTier(
                    choice.tier
                );

            if (
                tier &&
                counts[
                    tier
                ] !==
                undefined
            ) {

                counts[
                    tier
                ] +=
                    1;

            }

        }
    );

    return counts;

}

/* =========================================================
   STORAGE
========================================================= */

function saveChoices() {

    localStorage.setItem(
        "collegeconnect_choices",
        JSON.stringify(
            choices
        )
    );

}

function loadSavedChoices() {

    try {

        const saved =
            localStorage.getItem(
                "collegeconnect_choices"
            );

        if (
            !saved
        ) {

            return [];

        }

        const parsed =
            JSON.parse(
                saved
            );

        if (
            !Array.isArray(
                parsed
            )
        ) {

            return [];

        }

        return parsed.map(
            normalizeChoice
        );

    } catch {

        return [];

    }

}

/* =========================================================
   CLEAR MY CHOICE LIST
========================================================= */

clearChoicesButton?.addEventListener(
    "click",
    () => {

        if (
            choices.length ===
            0
        ) {

            return;

        }

        const confirmed =
            window.confirm(
                "Clear your entire My Choice List?"
            );

        if (
            !confirmed
        ) {

            return;

        }

        choices =
            [];

        saveChoices();

        renderChoices();

    }
);

/* =========================================================
   EXPORT CSV
========================================================= */

exportButton?.addEventListener(
    "click",
    () => {

        if (
            choices.length === 0
        ) {
            alert("There are no choices to export. Please add college–branch choices first.");
            return;
        }

        const headers = [
            "Preference",
            "College Code",
            "College Name",
            "Branch Code",
            "Branch Name",
            "District",
            "Latest Cutoff (2025)",
            "Latest Closing Rank (2025)",
            "Feasibility Tier",
            "Estimated Probability (%)",
            "Historical Fit Score (%)",
            "Strategy Reasoning"
        ];

        const rows = choices.map((choice, index) => [
            index + 1,
            choice.college_code ?? "",
            choice.college_name ?? "",
            choice.branch_code ?? "",
            choice.branch_name ?? "",
            choice.district ?? "",
            choice.latest_cutoff !== null && choice.latest_cutoff !== undefined ? Number(choice.latest_cutoff).toFixed(2) : "",
            choice.latest_closing_rank ?? "",
            choice.tier ?? "Target",
            choice.estimated_probability !== null && choice.estimated_probability !== undefined ? `${Number(choice.estimated_probability).toFixed(1)}%` : "",
            choice.historical_fit_score !== null && choice.historical_fit_score !== undefined ? `${Number(choice.historical_fit_score).toFixed(1)}%` : "",
            choice.probability_reasoning ?? ""
        ]);

        const csvString = [headers, ...rows]
            .map(row => row.map(csvEscape).join(","))
            .join("\r\n");

        // UTF-8 BOM (\uFEFF) ensures Excel and Google Sheets render Unicode and special characters perfectly
        const blob = new Blob(
            ["\uFEFF" + csvString],
            { type: "text/csv;charset=utf-8;" }
        );

        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        const dateStr = new Date().toISOString().slice(0, 10);
        link.download = `collegeconnect_choice_list_${dateStr}.csv`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }
);

/* =========================================================
   EXPORT PDF
========================================================= */

exportPdfButton?.addEventListener(
    "click",
    async () => {

        if (
            choices.length === 0
        ) {
            alert("There are no choices to export. Please add college–branch choices first.");
            return;
        }

        const originalText = exportPdfButton.textContent;
        exportPdfButton.textContent = "Generating PDF...";
        exportPdfButton.disabled = true;

        try {
            const studentProfile = {
                cutoff_mark: cutoffInput?.value ? parseFloat(cutoffInput.value) : (latestPredictionData?.student_input?.cutoff_mark || null),
                state_rank: stateRankInput?.value ? parseInt(stateRankInput.value, 10) : (latestPredictionData?.student_input?.state_rank || null),
                community: latestPredictionData?.student_input?.community || communitySelect?.value || "OC",
                quota: latestPredictionData?.student_input?.quota || counselingQuotaSelect?.value || "GENERAL"
            };

            const response = await fetch("/api/choices/export-pdf", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    choices: choices,
                    student_profile: studentProfile
                })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.message || `PDF export failed (HTTP ${response.status})`);
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            const dateStr = new Date().toISOString().slice(0, 10);
            link.download = `CollegeConnect_Choice_List_${dateStr}.pdf`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);

        } catch (err) {
            console.error("PDF export error:", err);
            alert(`Failed to export PDF: ${err.message}`);
        } finally {
            exportPdfButton.textContent = originalText;
            exportPdfButton.disabled = false;
        }
    }
);

exportDoteButton?.addEventListener(
    "click",
    () => {

        if (
            choices.length ===
            0
        ) {

            alert(
                "There are no choices to export."
            );

            return;

        }

        let text = "======================================================================\n";
        text += "TAMIL NADU ENGINEERING ADMISSIONS (TNEA) - COUNSELING CHOICE LIST\n";
        text += "Generated by CollegeConnect (Verified Historical Reference)\n";
        text += "======================================================================\n";
        text += `Total Selected Choices: ${choices.length}\n\n`;

        text += "CHOICE PREFERENCE ORDER:\n";
        choices.forEach((choice, index) => {
            const code = choice.college_code || "—";
            const name = choice.college_name || "—";
            const branchCode = choice.branch_code || "—";
            const branchName = choice.branch_name || "—";
            const tier = choice.tier || "Target";
            text += `[Choice ${index + 1}] Code: ${code} | ${name}\n`;
            text += `          Branch: ${branchCode} (${branchName}) [Tier: ${tier}]\n\n`;
        });

        text += "======================================================================\n";
        text += "FORMAT FOR DOTE PORTAL ENTRY (tneaonline.org):\n";
        text += "Choice_No\tCollege_Code\tBranch_Code\n";
        choices.forEach((choice, index) => {
            text += `${index + 1}\t\t${choice.college_code}\t\t${choice.branch_code}\n`;
        });
        text += "======================================================================\n";

        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                alert("Choice list successfully copied to clipboard in official DoTE format!\n\nYou can now paste it directly into your notes or counseling application.");
            }).catch(() => {
                downloadTextFile(text);
            });
        } else {
            downloadTextFile(text);
        }

        function downloadTextFile(content) {
            const blob = new Blob([content], { type: "text/plain;charset=utf-8;" });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = "collegeconnect_dote_choices.txt";
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);
        }

    }
);


function csvEscape(
    value
) {

    const text =
        value === null ||
        value === undefined
            ? ""
            : String(
                value
            );

    if (
        text.includes(
            ","
        ) ||
        text.includes(
            '"'
        ) ||
        text.includes(
            "\n"
        )
    ) {

        return (
            '"' +
            text.replaceAll(
                '"',
                '""'
            ) +
            '"'
        );

    }

    return text;

}

/* =========================================================
   MATRIX
========================================================= */

async function loadMatrixDistricts() {

    try {

        const response =
            await fetch(
                "/api/districts"
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            data.status !== "ok"
        ) {

            return;

        }

        matrixDistrict.innerHTML = `
            <option value="">
                All districts
            </option>
        `;

        data.districts.forEach(
            district => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    district;

                option.textContent =
                    district;

                matrixDistrict.appendChild(
                    option
                );

            }
        );

    } catch {

        // Ignore initial matrix errors.

    }

}

async function loadMatrixBranches() {

    try {

        const params =
            new URLSearchParams();

        if (
            matrixDistrict.value
        ) {

            params.set(
                "district",
                matrixDistrict.value
            );

        }

        const query =
            params.toString();

        const url =
            query
                ? `/api/branches?${query}`
                : "/api/branches";

        const response =
            await fetch(
                url
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            data.status !== "ok"
        ) {

            return;

        }

        matrixBranch.innerHTML = `
            <option value="">
                All branches
            </option>
        `;

        data.branches.forEach(
            branch => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    branch.branch_code;

                option.textContent =
                    `${branch.branch_code} - ${branch.branch_name}`;

                matrixBranch.appendChild(
                    option
                );

            }
        );

    } catch {

        // Ignore initial matrix errors.

    }

}

async function loadMatrixColleges() {

    try {

        const params =
            new URLSearchParams();

        if (
            matrixDistrict &&
            matrixDistrict.value
        ) {

            params.set(
                "district",
                matrixDistrict.value
            );

        }

        if (
            matrixBranch &&
            matrixBranch.value
        ) {

            params.set(
                "branch_code",
                matrixBranch.value
            );

        }

        const query =
            params.toString();

        const url =
            query
                ? `/api/colleges?${query}`
                : "/api/colleges";

        const response =
            await fetch(
                url
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            data.status !== "ok" ||
            !matrixCollege
        ) {

            return;

        }

        matrixCollege.innerHTML = `
            <option value="">
                All colleges
            </option>
        `;

        data.colleges.forEach(
            college => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    college.college_code;

                option.textContent =
                    `${college.college_code} - ${college.college_name}`;

                matrixCollege.appendChild(
                    option
                );

            }
        );

    } catch {

        // Ignore initial matrix errors.

    }

}

matrixDistrict?.addEventListener(
    "change",
    async () => {

        await loadMatrixBranches();
        await loadMatrixColleges();

    }
);

matrixBranch?.addEventListener(
    "change",
    async () => {

        await loadMatrixColleges();

    }
);

loadMatrixButton?.addEventListener(
    "click",
    async () => {

        hideMatrixError();

        if (
            !matrixCommunity.value
        ) {

            showMatrixError(
                "Please select a community."
            );

            return;

        }

        setMatrixLoading(
            true
        );

        try {

            const params =
                new URLSearchParams();

            params.set(
                "community",
                matrixCommunity.value
            );

            if (
                matrixDistrict.value
            ) {

                params.set(
                    "district",
                    matrixDistrict.value
                );

            }

            if (
                matrixBranch.value
            ) {

                params.set(
                    "branch_code",
                    matrixBranch.value
                );

            }

            if (
                matrixCollege &&
                matrixCollege.value
            ) {

                params.set(
                    "college_code",
                    matrixCollege.value
                );

            }

            const response =
                await fetch(
                    `/api/rank-matrix?${params.toString()}`
                );

            const data =
                await response.json();

            if (
                !response.ok ||
                data.status !== "ok"
            ) {

                throw new Error(
                    data.message ||
                    "Failed to load rank matrix."
                );

            }

            renderMatrix(
                data
            );

        } catch (
            error
        ) {

            showMatrixError(
                error.message
            );

        } finally {

            setMatrixLoading(
                false
            );

        }

    }
);

function renderMatrix(
    data
) {

    const results =
        data.results ||
        [];

    matrixTableBody.innerHTML =
        "";

    if (
        results.length ===
        0
    ) {

        matrixTableBody.innerHTML = `
            <tr>
                <td colspan="7">
                    No historical rank records found.
                </td>
            </tr>
        `;

    } else {

        results.forEach(
            (
                result,
                index
            ) => {

                const row =
                    document.createElement(
                        "tr"
                    );

                row.innerHTML = `

                    <td>
                        ${index + 1}
                    </td>

                    <td>

                        <div class="college-name">

                            ${escapeHtml(
                                result.college_name ||
                                "—"
                            )}

                        </div>

                        <div class="code-text">

                            Code:

                            ${escapeHtml(
                                String(
                                    result.college_code ??
                                    "—"
                                )
                            )}

                        </div>

                    </td>

                    <td>

                        ${escapeHtml(
                            result.branch_name ||
                            result.branch_code ||
                            "—"
                        )}

                    </td>

                    <td>

                        ${escapeHtml(
                            result.district ||
                            "—"
                        )}

                    </td>

                    <td>

                        ${escapeHtml(
                            String(
                                result.year ??
                                "—"
                            )
                        )}

                    </td>

                    <td>

                        ${escapeHtml(
                            String(
                                result.cutoff_mark ??
                                "—"
                            )
                        )}

                    </td>

                    <td>

                        ${escapeHtml(
                            String(
                                result.closing_rank ??
                                "—"
                            )
                        )}

                    </td>

                `;

                matrixTableBody.appendChild(
                    row
                );

            }
        );

    }

    matrixSection.classList.remove(
        "hidden"
    );

}

/* =========================================================
   CLEAR PREDICTOR
========================================================= */

clearButton?.addEventListener(
    "click",
    async () => {

        cutoffInput.value =
            "";

        stateRankInput.value =
            "";

        communitySelect.value =
            "";

        selectedDistricts =
            [];

        selectedBranches =
            [];

        selectedCollege =
            null;

        districtSearch.value =
            "";

        branchSearch.value =
            "";

        collegeSearch.value =
            "";

        latestResults =
            [];

        latestPredictionData =
            null;

        aiSuggestedChoices =
            [];

        activeResultFilter =
            "ALL";

        renderDistrictPicker();

        await loadBranches();

        renderBranchPicker();

        await loadColleges();

        renderCollegeSuggestions();

        renderSelectedCollege();

        resultsSection.classList.add(
            "hidden"
        );

        ragSection.classList.add(
            "hidden"
        );

        if (mathsMarksInput) mathsMarksInput.value = "";
        if (physicsMarksInput) physicsMarksInput.value = "";
        if (chemistryMarksInput) chemistryMarksInput.value = "";
        if (calcPreviewDisplay) calcPreviewDisplay.textContent = "Cutoff: — / 200";

        hideError();

        hideRagError();

        if (counselingQuotaSelect) {
            counselingQuotaSelect.value = "GENERAL";
        }

        if (quotaAdvisoryBanner) {
            quotaAdvisoryBanner.classList.add("hidden");
        }

        if (tierFilterSelect) {
            tierFilterSelect.value = "ALL";
        }

        renderAISuggestedList();

    }
);

/* =========================================================
   COUNSELING QUOTA SELECTION & ADVISORY
========================================================= */

counselingQuotaSelect?.addEventListener("change", () => {
    const val = counselingQuotaSelect.value;
    if (!quotaAdvisoryBanner) return;

    if (val === "GENERAL") {
        quotaAdvisoryBanner.classList.add("hidden");
    } else if (val === "GOVT_7_5") {
        if (quotaAdvisoryTitle) quotaAdvisoryTitle.textContent = "7.5% Government School Preferential Quota";
        if (quotaAdvisoryDesc) quotaAdvisoryDesc.textContent = "In Tamil Nadu TNEA counseling, Government school students (7.5% reservation) participate in dedicated preliminary counseling rounds administered directly by DoTE. Historical cutoffs displayed below represent General Academic benchmarks; for the 7.5% quota, closing cutoffs typically operate 15–30 marks lower at premier Tier-1/Tier-2 colleges. Use these results as a reliable reference baseline.";
        quotaAdvisoryBanner.classList.remove("hidden");
    } else if (val === "SPECIAL_SPORTS") {
        if (quotaAdvisoryTitle) quotaAdvisoryTitle.textContent = "Special Reservation: Sports Quota";
        if (quotaAdvisoryDesc) quotaAdvisoryDesc.textContent = "Sports quota seats (500 seats allocated by DoTE) are allotted through in-person certificate verification and dedicated sports counseling rounds before general academic rounds. General cutoffs represent a quality and prestige benchmark.";
        quotaAdvisoryBanner.classList.remove("hidden");
    } else if (val === "SPECIAL_EXSERVICE") {
        if (quotaAdvisoryTitle) quotaAdvisoryTitle.textContent = "Special Reservation: Ex-Servicemen Quota";
        if (quotaAdvisoryDesc) quotaAdvisoryDesc.textContent = "Wards of Ex-Servicemen receive special preliminary allotment by DoTE prior to general rounds. General cutoffs reflect academic standards across institutions.";
        quotaAdvisoryBanner.classList.remove("hidden");
    } else if (val === "SPECIAL_PWD") {
        if (quotaAdvisoryTitle) quotaAdvisoryTitle.textContent = "Special Reservation: Differently Abled (PWD)";
        if (quotaAdvisoryDesc) quotaAdvisoryDesc.textContent = "Differently Abled (PWD) reservation is conducted through dedicated medical board verification and early priority allotment. General cutoffs reflect standard baseline thresholds.";
        quotaAdvisoryBanner.classList.remove("hidden");
    }
});

/* =========================================================
   CLASS 12 CUTOFF CALCULATOR
========================================================= */

function calculateCutoffFromMarks() {
    const m = parseFloat(mathsMarksInput?.value);
    const p = parseFloat(physicsMarksInput?.value);
    const c = parseFloat(chemistryMarksInput?.value);

    if (isNaN(m) || isNaN(p) || isNaN(c)) {
        if (calcPreviewDisplay) {
            calcPreviewDisplay.textContent = "Cutoff: — / 200";
        }
        return null;
    }

    if (m < 0 || m > 100 || p < 0 || p > 100 || c < 0 || c > 100) {
        if (calcPreviewDisplay) {
            calcPreviewDisplay.textContent = "Marks: 0 to 100";
        }
        return null;
    }

    const cutoff = m + (p / 2.0) + (c / 2.0);
    const rounded = Math.round(cutoff * 1000) / 1000;
    if (calcPreviewDisplay) {
        calcPreviewDisplay.textContent = `Cutoff: ${rounded.toFixed(2)} / 200`;
    }
    return rounded;
}

toggleCalcButton?.addEventListener("click", () => {
    calculatorPanel?.classList.toggle("hidden");
    if (!calculatorPanel?.classList.contains("hidden")) {
        toggleCalcButton.textContent = "Close Calculator";
        mathsMarksInput?.focus();
    } else {
        toggleCalcButton.textContent = "Calculate from Marks";
    }
});

[mathsMarksInput, physicsMarksInput, chemistryMarksInput].forEach(inp => {
    inp?.addEventListener("input", calculateCutoffFromMarks);
});

applyCutoffButton?.addEventListener("click", () => {
    const cutoff = calculateCutoffFromMarks();
    if (cutoff !== null) {
        cutoffInput.value = cutoff.toFixed(2);
        stateRankInput.value = "";
        calculatorPanel?.classList.add("hidden");
        if (toggleCalcButton) {
            toggleCalcButton.textContent = "Calculate from Marks";
        }
        hideError();
    } else {
        alert("Please enter valid marks (0–100) for Maths, Physics, and Chemistry.");
    }
});


/* =========================================================
   UI HELPERS
========================================================= */

function setLoading(
    visible
) {

    loading.classList.toggle(
        "hidden",
        !visible
    );

}

function showError(
    message
) {

    errorMessage.textContent =
        message;

    errorMessage.classList.remove(
        "hidden"
    );

}

function hideError() {

    errorMessage.textContent =
        "";

    errorMessage.classList.add(
        "hidden"
    );

}

function showRagError(
    message
) {

    ragError.textContent =
        message;

    ragError.classList.remove(
        "hidden"
    );

}

function hideRagError() {

    ragError.textContent =
        "";

    ragError.classList.add(
        "hidden"
    );

}

function setMatrixLoading(
    visible
) {

    matrixLoading.classList.toggle(
        "hidden",
        !visible
    );

}

function showMatrixError(
    message
) {

    matrixError.textContent =
        message;

    matrixError.classList.remove(
        "hidden"
    );

}

function hideMatrixError() {

    matrixError.textContent =
        "";

    matrixError.classList.add(
        "hidden"
    );

}

/* =========================================================
   DISPLAY HELPERS
========================================================= */

function formatProbability(
    value
) {

    if (
        value ===
            null ||
        value ===
            undefined
    ) {

        return "—";

    }

    const number =
        Number(
            value
        );

    if (
        !Number.isFinite(
            number
        )
    ) {

        return "—";

    }

    return `${number.toFixed(
        1
    )}%`;

}

function getTierColor(
    tier
) {

    const isLight = document.documentElement.getAttribute("data-theme") === "light";

    if (
        tier ===
        "Safe"
    ) {

        return {

            border:
                isLight ? "rgba(5, 150, 105, 0.45)" : "rgba(16,185,129,0.22)",

            background:
                isLight ? "#ecfdf5" : "rgba(16,185,129,0.10)",

            text:
                isLight ? "#047857" : "#10b981"

        };

    }

    if (
        tier ===
        "Reach"
    ) {

        return {

            border:
                isLight ? "rgba(225, 29, 72, 0.40)" : "rgba(239,68,68,0.22)",

            background:
                isLight ? "#fff1f2" : "rgba(239,68,68,0.10)",

            text:
                isLight ? "#be123c" : "#ef4444"

        };

    }

    return {

        border:
            isLight ? "rgba(217, 119, 6, 0.45)" : "rgba(245,158,11,0.22)",

        background:
            isLight ? "#fffbeb" : "rgba(245,158,11,0.10)",

        text:
            isLight ? "#b45309" : "#f59e0b"

    };

}

function compareProbabilityDescending(
    a,
    b
) {

    return (
        Number(
            b.estimated_probability
        ) -
        Number(
            a.estimated_probability
        )
    );

}

function choiceKey(
    choice
) {

    return (
        `${choice.college_code}::${choice.branch_code}`
    );

}

function escapeHtml(
    value
) {

    return String(
        value
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}

/* =========================================================
   HISTORICAL 5-YEAR TREND & BRANCH SWAP MODALS
========================================================= */

const trendModal = document.getElementById("trendModal");
const trendModalTitle = document.getElementById("trendModalTitle");
const trendModalSubtitle = document.getElementById("trendModalSubtitle");
const trendModalClose = document.getElementById("trendModalClose");
const trendModalLoading = document.getElementById("trendModalLoading");
const trendModalContent = document.getElementById("trendModalContent");
const trendLegendText = document.getElementById("trendLegendText");
const trendChartSvgContainer = document.getElementById("trendChartSvgContainer");
const trendMetricsCard = document.getElementById("trendMetricsCard");
const trendTableBody = document.getElementById("trendTableBody");

const branchSwapModal = document.getElementById("branchSwapModal");
const branchSwapModalTitle = document.getElementById("branchSwapModalTitle");
const branchSwapModalSubtitle = document.getElementById("branchSwapModalSubtitle");
const branchSwapModalClose = document.getElementById("branchSwapModalClose");
const branchSwapModalLoading = document.getElementById("branchSwapModalLoading");
const branchSwapModalContent = document.getElementById("branchSwapModalContent");
const branchSwapTableBody = document.getElementById("branchSwapTableBody");

function closeTrendModal() {
    if (trendModal) {
        trendModal.classList.add("hidden");
    }
}

function closeBranchSwapModal() {
    if (branchSwapModal) {
        branchSwapModal.classList.add("hidden");
    }
}

if (trendModalClose) {
    trendModalClose.addEventListener("click", closeTrendModal);
}

if (branchSwapModalClose) {
    branchSwapModalClose.addEventListener("click", closeBranchSwapModal);
}

// Close on backdrop click
[trendModal, branchSwapModal].forEach(modalEl => {
    if (modalEl) {
        modalEl.addEventListener("click", (evt) => {
            if (evt.target === modalEl) {
                modalEl.classList.add("hidden");
            }
        });
    }
});

// Close on ESC key
window.addEventListener("keydown", (evt) => {
    if (evt.key === "Escape") {
        closeTrendModal();
        closeBranchSwapModal();
    }
});

async function openTrendModal(result) {
    if (!trendModal) return;

    const collegeName = result.college_name || `College ${result.college_code}`;
    const branchCode = result.branch_code || "";
    const community = result.community || latestPredictionData?.student_input?.community || communitySelect?.value || "OC";
    const quota = result.quota || latestPredictionData?.student_input?.quota || counselingQuotaSelect?.value || "GENERAL";

    // Format title exactly like reference screenshot: "College Name (BranchCode)"
    trendModalTitle.textContent = `${collegeName} (${branchCode})`;
    if (trendLegendText) {
        trendLegendText.textContent = `Closing Cutoff Score (${community})`;
    }

    trendModal.classList.remove("hidden");
    trendModalLoading.classList.remove("hidden");
    trendModalContent.classList.add("hidden");

    try {
        const params = new URLSearchParams({
            college_code: result.college_code,
            branch_code: result.branch_code,
            community: community,
            quota: quota
        });

        const resp = await fetch(`/api/historical?${params.toString()}`);
        if (!resp.ok) {
            throw new Error(`Failed to load historical data (HTTP ${resp.status})`);
        }

        const data = await resp.json();
        if (data.status !== "ok" || !data.years || data.years.length === 0) {
            trendModalLoading.classList.add("hidden");
            trendModalContent.classList.remove("hidden");
            if (trendMetricsCard) {
                trendMetricsCard.innerHTML = `<div style="grid-column: 1/-1; color: #94a3b8; padding: 12px;">No historical cutoff records found for ${escapeHtml(community)} category in ${escapeHtml(quota)} quota.</div>`;
            }
            if (trendChartSvgContainer) {
                trendChartSvgContainer.innerHTML = "";
            }
            if (trendTableBody) {
                trendTableBody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#94a3b8; padding:20px;">No admission data available.</td></tr>`;
            }
            return;
        }

        const rows = data.years.sort((a, b) => Number(a.year) - Number(b.year));
        const validRecords = rows.filter(
            r => r.cutoff_mark !== null && r.cutoff_mark !== undefined && !isNaN(Number(r.cutoff_mark))
        );
        const validCutoffs = validRecords.map(r => Number(r.cutoff_mark));

        // 1. 5-YR AVG CUTOFF
        const avgCutoff = validCutoffs.length
            ? (validCutoffs.reduce((a, b) => a + b, 0) / validCutoffs.length).toFixed(2)
            : "—";

        // 2. PEAK CUTOFF
        const peakCutoff = validCutoffs.length
            ? Math.max(...validCutoffs).toFixed(2)
            : "—";

        // 3. 5-YR SCORE SHIFT
        let shiftFormatted = "0.00";
        let shiftClass = "val-shift-neutral";
        let shiftVal = 0;
        if (validCutoffs.length >= 2) {
            const firstCut = validCutoffs[0];
            const lastCut = validCutoffs[validCutoffs.length - 1];
            shiftVal = lastCut - firstCut;
            shiftFormatted = shiftVal > 0 ? `+${shiftVal.toFixed(2)}` : shiftVal.toFixed(2);
            shiftClass = shiftVal > 0 ? "val-shift-pos" : (shiftVal < 0 ? "val-shift-neg" : "val-shift-neutral");
        } else if (validCutoffs.length === 1) {
            shiftFormatted = "0.00";
        }

        // 4. DEMAND TRAJECTORY
        let trajectory = "Stable Demand";
        if (validCutoffs.length >= 2) {
            if (Number(peakCutoff) >= 199.0 || Math.abs(shiftVal) <= 0.75) {
                trajectory = "Stable Demand";
            } else if (shiftVal > 0.75) {
                trajectory = "Surging Demand";
            } else if (shiftVal < -0.75) {
                trajectory = "Easing Cutoff";
            }
        } else {
            trajectory = "Emerging Branch";
        }

        // Render 4-Column Summary Card matching reference screenshot
        if (trendMetricsCard) {
            trendMetricsCard.innerHTML = `
                <div class="trend-metric-item">
                    <span class="trend-metric-label">5-YR AVG CUTOFF</span>
                    <span class="trend-metric-val val-avg">${avgCutoff}</span>
                </div>
                <div class="trend-metric-item">
                    <span class="trend-metric-label">PEAK CUTOFF</span>
                    <span class="trend-metric-val val-peak">${peakCutoff}</span>
                </div>
                <div class="trend-metric-item">
                    <span class="trend-metric-label">5-YR SCORE SHIFT</span>
                    <span class="trend-metric-val ${shiftClass}">${shiftFormatted}</span>
                </div>
                <div class="trend-metric-item">
                    <span class="trend-metric-label">DEMAND TRAJECTORY</span>
                    <span class="trend-metric-val val-trajectory">${trajectory}</span>
                </div>
            `;
        }

        // Render Spline SVG Chart
        currentTrendData = { rows, validRecords };
        renderTrendSvgChart(rows, validRecords);

        // Populate detailed table
        if (trendTableBody) {
            const isLight = document.documentElement.getAttribute("data-theme") === "light";
            trendTableBody.innerHTML = rows.map(r => {
                const cut = r.cutoff_mark !== null && r.cutoff_mark !== undefined ? Number(r.cutoff_mark).toFixed(2) : "Not Allotted";
                const rank = r.closing_rank ? Number(r.closing_rank).toLocaleString() : "—";
                const completeness = r.is_partial
                    ? `<span style="color:#f59e0b; font-size:0.75rem;">⚠ Partial</span>`
                    : `<span style="color:#10b981; font-size:0.75rem;">✓ Full</span>`;
                return `
                    <tr>
                        <td><strong>${escapeHtml(r.year)}</strong></td>
                        <td style="color:${isLight ? '#4f46e5' : '#818cf8'}; font-weight:700;">${cut}</td>
                        <td>${rank}</td>
                        <td>${completeness}</td>
                    </tr>
                `;
            }).join("");
        }

        trendModalLoading.classList.add("hidden");
        trendModalContent.classList.remove("hidden");

    } catch (err) {
        console.error("Error opening trend modal:", err);
        trendModalLoading.classList.add("hidden");
        trendModalContent.classList.remove("hidden");
        if (trendMetricsCard) {
            trendMetricsCard.innerHTML = `<div style="grid-column: 1/-1; color: #ef4444; padding: 12px;">Error loading data: ${escapeHtml(err.message)}</div>`;
        }
        if (trendChartSvgContainer) {
            trendChartSvgContainer.innerHTML = "";
        }
    }
}

function renderTrendSvgChart(rows, validRecords) {
    if (!trendChartSvgContainer) return;

    const isLight = document.documentElement.getAttribute("data-theme") === "light";

    if (!validRecords.length) {
        trendChartSvgContainer.innerHTML = `<div style="text-align:center; color:${isLight ? '#64748b' : '#94a3b8'}; padding-top:90px; font-size:0.88rem;">No cutoff data available to plot chart.</div>`;
        return;
    }

    const width = 680;
    const height = 240;
    const padLeft = 60;
    const padRight = 35;
    const padTop = 20;
    const padBottom = 35;

    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    const validCutoffs = validRecords.map(r => Number(r.cutoff_mark));
    const minVal = Math.min(...validCutoffs);
    const maxVal = Math.max(...validCutoffs);
    const span = maxVal - minVal;

    let step = 0.5;
    if (span > 30) step = 5.0;
    else if (span > 15) step = 2.5;
    else if (span > 7) step = 1.0;
    else step = 0.5;

    let yMin = Math.floor(minVal / step) * step;
    let yMax = Math.ceil(maxVal / step) * step;

    if (yMax === yMin) {
        yMax = Math.min(200, yMax + step * 2);
        yMin = Math.max(0, yMin - step * 2);
    } else {
        yMin = Math.max(0, yMin - step);
        yMax = Math.min(200, yMax + step);
    }

    const valToY = (val) => {
        const ratio = (val - yMin) / (yMax - yMin);
        return padTop + plotH - (ratio * plotH);
    };

    const gridStroke = isLight ? "#e2e8f0" : "rgba(255,255,255,0.06)";
    const yLabelFill = isLight ? "#475569" : "#64748b";
    const xLabelFill = isLight ? "#475569" : "#94a3b8";
    const curveStroke = isLight ? "#4f46e5" : "#818cf8";
    const markerStroke = isLight ? "#4f46e5" : "#818cf8";
    const gradientOpacity = isLight ? "0.16" : "0.30";

    // Horizontal grid lines and Y-axis labels
    let gridLinesSvg = "";
    let yLabelsSvg = "";
    const totalTicks = Math.round((yMax - yMin) / step);
    for (let i = 0; i <= totalTicks; i++) {
        const tickVal = yMax - (i * step);
        if (tickVal < yMin - 1e-6) break;
        const yPos = valToY(tickVal);
        gridLinesSvg += `<line x1="${padLeft}" y1="${yPos.toFixed(1)}" x2="${padLeft + plotW}" y2="${yPos.toFixed(1)}" stroke="${gridStroke}" />`;
        yLabelsSvg += `<text x="${padLeft - 12}" y="${(yPos + 4).toFixed(1)}" fill="${yLabelFill}" font-size="11" font-weight="500" text-anchor="end">${tickVal.toFixed(1)}</text>`;
    }

    // X-axis labels: 2021 Counseling ... 2025 Counseling
    const allYears = [2021, 2022, 2023, 2024, 2025];
    let xLabelsSvg = "";
    allYears.forEach((yr, idx) => {
        const xPos = padLeft + (idx / (allYears.length - 1)) * plotW;
        xLabelsSvg += `<text x="${xPos.toFixed(1)}" y="${height - 10}" fill="${xLabelFill}" font-size="11" text-anchor="middle" font-weight="500">${yr} Counseling</text>`;
    });

    // Map existing points
    const points = [];
    allYears.forEach((yr, idx) => {
        const rec = validRecords.find(r => Number(r.year) === yr);
        if (rec) {
            const x = padLeft + (idx / (allYears.length - 1)) * plotW;
            const y = valToY(Number(rec.cutoff_mark));
            points.push({
                year: yr,
                cutoff: Number(rec.cutoff_mark),
                rank: rec.closing_rank,
                x,
                y
            });
        }
    });

    let pathD = "";
    let areaD = "";
    let circlesSvg = "";

    // Smooth cubic spline curve (Catmull-Rom cubic Bezier)
    if (points.length === 1) {
        pathD = `M ${padLeft} ${points[0].y.toFixed(1)} L ${padLeft + plotW} ${points[0].y.toFixed(1)}`;
        areaD = `${pathD} L ${padLeft + plotW} ${(padTop + plotH).toFixed(1)} L ${padLeft} ${(padTop + plotH).toFixed(1)} Z`;
    } else if (points.length > 1) {
        pathD = `M ${points[0].x.toFixed(1)} ${points[0].y.toFixed(1)}`;
        for (let i = 0; i < points.length - 1; i++) {
            const p0 = i > 0 ? points[i - 1] : points[i];
            const p1 = points[i];
            const p2 = points[i + 1];
            const p3 = i < points.length - 2 ? points[i + 2] : p2;

            const cp1x = p1.x + (p2.x - p0.x) / 6;
            const cp1y = p1.y + (p2.y - p0.y) / 6;
            const cp2x = p2.x - (p3.x - p1.x) / 6;
            const cp2y = p2.y - (p3.y - p1.y) / 6;

            pathD += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
        }
        areaD = `${pathD} L ${points[points.length - 1].x.toFixed(1)} ${(padTop + plotH).toFixed(1)} L ${points[0].x.toFixed(1)} ${(padTop + plotH).toFixed(1)} Z`;
    }

    // Glowing circular points with purple/indigo stroke
    points.forEach(pt => {
        const rankStr = pt.rank ? ` • Closing Rank: ${Number(pt.rank).toLocaleString()}` : '';
        circlesSvg += `
            <circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(1)}" r="5.5" fill="#ffffff" stroke="${markerStroke}" stroke-width="3">
                <title>${pt.year} Counseling: ${pt.cutoff.toFixed(2)}${rankStr}</title>
            </circle>
        `;
    });

    trendChartSvgContainer.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid meet">
            <defs>
                <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#6366f1" stop-opacity="${gradientOpacity}" />
                    <stop offset="100%" stop-color="#6366f1" stop-opacity="0.0" />
                </linearGradient>
            </defs>
            ${gridLinesSvg}
            ${yLabelsSvg}
            ${xLabelsSvg}
            ${areaD ? `<path d="${areaD}" fill="url(#trendGradient)" />` : ""}
            ${pathD ? `<path d="${pathD}" fill="none" stroke="${curveStroke}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" />` : ""}
            ${circlesSvg}
        </svg>
    `;
}

async function openBranchSwapModal(result) {
    if (!branchSwapModal) return;

    const collegeName = result.college_name || `College ${result.college_code}`;
    const district = result.district || "";
    const community = result.community || latestPredictionData?.student_input?.community || communitySelect?.value || "OC";
    const quota = result.quota || latestPredictionData?.student_input?.quota || counselingQuotaSelect?.value || "GENERAL";

    branchSwapModalSubtitle.textContent = `${collegeName} (${district}) • Community: ${community}`;
    branchSwapModal.classList.remove("hidden");
    branchSwapModalLoading.classList.remove("hidden");
    branchSwapModalContent.classList.add("hidden");

    try {
        const cutoffVal = cutoffInput?.value?.trim() || latestPredictionData?.student_input?.cutoff_mark || "";
        const rankVal = stateRankInput?.value?.trim() || latestPredictionData?.student_input?.state_rank || "";

        const params = new URLSearchParams({
            college_code: result.college_code,
            community: community,
            quota: quota,
            cutoff_mark: cutoffVal,
            state_rank: rankVal
        });

        const resp = await fetch(`/api/branch-swap?${params.toString()}`);
        if (!resp.ok) {
            throw new Error(`Failed to load branch swap data (HTTP ${resp.status})`);
        }

        const data = await resp.json();
        if (data.status !== "ok" || !data.branches || data.branches.length === 0) {
            branchSwapModalLoading.classList.add("hidden");
            branchSwapModalContent.classList.remove("hidden");
            branchSwapTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#94a3b8; padding:20px;">No other engineering branches found for this institution.</td></tr>`;
            return;
        }

        branchSwapTableBody.innerHTML = data.branches.map(b => {
            const cut = b.latest_cutoff !== null ? Number(b.latest_cutoff).toFixed(2) : "—";
            const rnk = b.latest_closing_rank !== null ? Number(b.latest_closing_rank).toLocaleString() : "—";
            const avg = b.average_cutoff !== null ? Number(b.average_cutoff).toFixed(2) : "—";
            
            let cushionDisplay = "—";
            if (b.cushion !== null && b.cushion !== undefined) {
                const cVal = Number(b.cushion);
                const color = cVal >= 0 ? "#10b981" : "#ef4444";
                const prefix = cVal > 0 ? "+" : "";
                cushionDisplay = `<span style="color:${color}; font-weight:700;">${prefix}${cVal.toFixed(2)}</span>`;
            }

            const tier = b.tier || "Target";
            const tierCls = tier.toLowerCase();
            const isOriginal = String(b.branch_code).toUpperCase() === String(result.branch_code).toUpperCase();

            return `
                <tr style="${isOriginal ? 'background: rgba(99, 102, 241, 0.12);' : ''}">
                    <td>
                        <strong style="color:#f8fafc;">${escapeHtml(b.branch_code)}</strong> - 
                        <span style="color:#cbd5e1;">${escapeHtml(b.branch_name)}</span>
                        ${isOriginal ? '<span style="font-size:0.7rem; color:#818cf8; margin-left:6px; font-weight:700;">(CURRENT)</span>' : ''}
                    </td>
                    <td style="color:#38bdf8; font-weight:600;">${cut}</td>
                    <td>${rnk}</td>
                    <td>${avg}</td>
                    <td>${cushionDisplay}</td>
                    <td>
                        <span class="tier-badge tier-${tierCls}">
                            ${tierEmoji(tier)} ${escapeHtml(tier)}
                        </span>
                    </td>
                    <td>
                        <button 
                            type="button" 
                            class="branch-swap-add-btn" 
                            data-code="${escapeHtml(b.branch_code)}"
                            data-name="${escapeHtml(b.branch_name)}"
                            data-cut="${b.latest_cutoff || ''}"
                            data-rnk="${b.latest_closing_rank || ''}"
                            data-tier="${tier}"
                        >
                            + Add
                        </button>
                    </td>
                </tr>
            `;
        }).join("");

        // Attach add handlers for each branch
        branchSwapTableBody.querySelectorAll(".branch-swap-add-btn").forEach(btn => {
            const bCode = btn.dataset.code;
            const bName = btn.dataset.name;
            const bTier = btn.dataset.tier;
            const bCut = btn.dataset.cut ? Number(btn.dataset.cut) : null;
            const bRnk = btn.dataset.rnk ? Number(btn.dataset.rnk) : null;

            btn.addEventListener("click", () => {
                const added = addChoice({
                    college_code: result.college_code,
                    college_name: result.college_name,
                    district: result.district,
                    branch_code: bCode,
                    branch_name: bName,
                    tier: bTier,
                    latest_cutoff: bCut,
                    latest_closing_rank: bRnk,
                    estimated_probability: bTier === "Safe" ? 85 : (bTier === "Target" ? 55 : 20)
                });
                btn.textContent = added ? "Added ✓" : "Already Added";
                btn.disabled = true;
            });
        });

        branchSwapModalLoading.classList.add("hidden");
        branchSwapModalContent.classList.remove("hidden");

    } catch (err) {
        console.error("Error opening branch swap modal:", err);
        branchSwapModalLoading.classList.add("hidden");
        branchSwapModalContent.classList.remove("hidden");
        branchSwapTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#ef4444; padding:20px;">Error: ${escapeHtml(err.message)}</td></tr>`;
    }
}
/* ============================================================
   MY BRAND — VIRTUAL TRY-ON
   Connects the product page to the Flask virtual fitting room.
   ============================================================ */

const VIRTUAL_TRYON_API = "http://127.0.0.1:5000";

let cameraRunning = false;
let currentTryOnProduct = null;


/* ============================================================
   OPEN VIRTUAL FITTING ROOM
   ============================================================ */

function openVirtualFittingRoom(product = null) {

    currentTryOnProduct = product;
    window.activeTryOnProduct = product;

    const modal = document.getElementById("tryonModal");
    const preview = document.getElementById("tryonPreview");
    const overlay = document.getElementById("overlay");

    if (!modal) {
        console.error("ERROR: #tryonModal not found.");
        return;
    }

    /*
     * Reset preview every time the modal opens.
     */
    if (preview) {

        preview.innerHTML = `
            <div class="tryon-placeholder">

                <div class="tryon-icon">
                    ◉
                </div>

                <p>
                    Virtual fitting preview will appear here
                </p>

                <small>
                    ${
                        product
                            ? `Ready to try on ${escapeHtml(product.name)}`
                            : `Select a product to start your virtual fitting`
                    }
                </small>

            </div>
        `;
    }

    /*
     * IMPORTANT:
     * Add BOTH possible modal classes.
     *
     * This makes the code work whether your CSS
     * uses .modal.open or .modal.show.
     */
    modal.classList.add("open");
    modal.classList.add("show");

    if (overlay) {
        overlay.classList.add("active");
        overlay.classList.add("show");
    }

    console.log("Virtual Try-On modal opened.");
    console.log("Selected product:", product);
}


/* ============================================================
   CLOSE VIRTUAL FITTING ROOM
   ============================================================ */

async function closeVirtualFittingRoom() {

    const modal = document.getElementById("tryonModal");
    const overlay = document.getElementById("overlay");

    if (modal) {
        modal.classList.remove("open");
        modal.classList.remove("show");
    }

    if (overlay) {
        overlay.classList.remove("active");
        overlay.classList.remove("show");
    }

    currentTryOnProduct = null;
    window.activeTryOnProduct = null;

    if (cameraRunning) {

        try {
            await stopCamera();
        } catch (error) {
            console.error("Camera stop error:", error);
        }
    }
}


/* ============================================================
   OPEN CAMERA
   ============================================================ */

async function openCamera() {

    const product =
        currentTryOnProduct ||
        window.activeTryOnProduct;

    if (!product) {

        showTryOnError(
            "Please select a product first."
        );

        return;
    }

    console.log(
        "Opening camera for:",
        product
    );

    try {

        showTryOnLoading(
            "Starting camera..."
        );


        /*
         * 1. Start Flask camera
         */

        const startResponse = await fetch(
            `${VIRTUAL_TRYON_API}/start-camera`
        );

        if (!startResponse.ok) {

            throw new Error(
                `Camera start failed: ${startResponse.status}`
            );
        }

        const startData =
            await startResponse.json();

        console.log(
            "Camera response:",
            startData
        );


        if (
            startData.status !==
            "camera started"
        ) {

            throw new Error(
                "Flask could not start the camera."
            );
        }


        /*
         * 2. Select clothing
         */

        await selectClothing(product);


        /*
         * 3. Display Flask MJPEG stream
         */

        const preview =
            document.getElementById(
                "tryonPreview"
            );

        if (!preview) {

            throw new Error(
                "tryonPreview element not found."
            );
        }


        preview.innerHTML = `

            <div class="camera-wrapper">

                <img
                    id="virtualCameraFeed"
                    src="${VIRTUAL_TRYON_API}/video?t=${Date.now()}"
                    alt="Virtual fitting room camera"
                    class="virtual-camera-feed"
                >

                <div class="camera-status">

                    <span class="camera-dot"></span>

                    LIVE

                </div>

            </div>

        `;


        cameraRunning = true;


        console.log(
            "Virtual camera started."
        );


        showTryOnMessage(
            `${product.name} selected`
        );


    } catch (error) {

        console.error(
            "Virtual Try-On error:",
            error
        );

        showTryOnError(
            error.message ||
            "Unable to start the virtual fitting room."
        );

        cameraRunning = false;
    }
}


/* ============================================================
   SELECT CLOTHING
   ============================================================ */

async function selectClothing(product) {

    if (!product) {

        throw new Error(
            "No product supplied."
        );
    }


    if (!product.tryOnImage) {

        throw new Error(
            `No try-on image defined for ${product.name}`
        );
    }


    const filename =
        product.tryOnImage;

    const garmentType =
        product.garmentType ||
        "upper-body";


    console.log(
        "Selecting clothing:",
        filename,
        garmentType
    );


    const response = await fetch(
        `${VIRTUAL_TRYON_API}/set-clothing`,
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({

                filename:
                    filename,

                type:
                    garmentType

            })
        }
    );


    if (!response.ok) {

        let errorMessage =
            `Clothing selection failed: ${response.status}`;

        try {

            const errorData =
                await response.json();

            if (errorData.message) {

                errorMessage =
                    errorData.message;
            }

        } catch (_) {

            // Ignore JSON parsing failure.

        }

        throw new Error(
            errorMessage
        );
    }


    const data =
        await response.json();


    console.log(
        "Clothing selected:",
        data
    );


    return data;
}


/* ============================================================
   START VIRTUAL TRY-ON
   ============================================================ */

async function startVirtualTryOn(product) {

    const selectedProduct =
        product ||
        currentTryOnProduct ||
        window.activeTryOnProduct;


    if (!selectedProduct) {

        showTryOnError(
            "Please select a product first."
        );

        return;
    }


    currentTryOnProduct =
        selectedProduct;

    window.activeTryOnProduct =
        selectedProduct;


    console.log(
        "Starting Virtual Try-On:",
        selectedProduct
    );


    /*
     * If camera isn't running,
     * start it.
     */

    if (!cameraRunning) {

        await openCamera();

        return;
    }


    /*
     * Camera is already running.
     * Change clothing.
     */

    try {

        showTryOnLoading(
            "Changing clothing..."
        );


        await selectClothing(
            selectedProduct
        );


        restoreCameraFeed();


        showTryOnMessage(
            `${selectedProduct.name} selected`
        );


    } catch (error) {

        console.error(error);

        showTryOnError(
            error.message ||
            "Could not change clothing."
        );
    }
}


/* ============================================================
   CHANGE CLOTHING
   ============================================================ */

async function changeVirtualClothing(product) {

    if (!product) {
        return;
    }


    currentTryOnProduct =
        product;

    window.activeTryOnProduct =
        product;


    try {

        await selectClothing(
            product
        );


        console.log(
            "Changed clothing to:",
            product.name
        );


    } catch (error) {

        console.error(
            "Clothing change failed:",
            error
        );


        showTryOnError(
            error.message ||
            "Could not change clothing."
        );
    }
}


/* ============================================================
   STOP CAMERA
   ============================================================ */

async function stopCamera() {

    try {

        const response =
            await fetch(
                `${VIRTUAL_TRYON_API}/stop-camera`
            );


        if (!response.ok) {

            console.warn(
                "Stop camera request failed:",
                response.status
            );
        }


    } catch (error) {

        console.error(
            "Error stopping camera:",
            error
        );


    } finally {

        cameraRunning = false;


        const feed =
            document.getElementById(
                "virtualCameraFeed"
            );


        if (feed) {

            feed.src = "";
        }
    }
}


/* ============================================================
   RESTORE CAMERA FEED
   ============================================================ */

function restoreCameraFeed() {

    const preview =
        document.getElementById(
            "tryonPreview"
        );


    if (!preview) {
        return;
    }


    preview.innerHTML = `

        <div class="camera-wrapper">

            <img
                id="virtualCameraFeed"
                src="${VIRTUAL_TRYON_API}/video?t=${Date.now()}"
                alt="Virtual fitting room camera"
                class="virtual-camera-feed"
            >

            <div class="camera-status">

                <span class="camera-dot"></span>

                LIVE

            </div>

        </div>

    `;
}


/* ============================================================
   UPLOAD PHOTO
   ============================================================ */

function uploadPhotoPlaceholder() {

    showTryOnMessage(
        "Photo upload will be available soon."
    );
}


/* ============================================================
   LOADING UI
   ============================================================ */

function showTryOnLoading(message) {

    const preview =
        document.getElementById(
            "tryonPreview"
        );


    if (!preview) {
        return;
    }


    preview.innerHTML = `

        <div class="tryon-loading">

            <div class="tryon-spinner"></div>

            <p>
                ${escapeHtml(message)}
            </p>

        </div>

    `;
}


/* ============================================================
   ERROR UI
   ============================================================ */

function showTryOnError(message) {

    const preview =
        document.getElementById(
            "tryonPreview"
        );


    if (!preview) {
        return;
    }


    preview.innerHTML = `

        <div class="tryon-error">

            <div class="tryon-error-icon">
                ⚠
            </div>

            <h3>
                Virtual Try-On Error
            </h3>

            <p>
                ${escapeHtml(message)}
            </p>

            <button
                type="button"
                class="btn btn-outline"
                onclick="openCamera()"
            >
                Try Again
            </button>

        </div>

    `;
}


/* ============================================================
   MESSAGE / TOAST
   ============================================================ */

function showTryOnMessage(message) {

    if (
        typeof showToast ===
        "function"
    ) {

        showToast(message);

        return;
    }


    const toast =
        document.getElementById(
            "toast"
        );


    if (!toast) {

        console.log(message);

        return;
    }


    toast.textContent =
        message;


    toast.classList.add(
        "show"
    );


    setTimeout(() => {

        toast.classList.remove(
            "show"
        );

    }, 3000);
}


/* ============================================================
   HTML ESCAPE
   ============================================================ */

function escapeHtml(value) {

    return String(value)

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


/* ============================================================
   CLEANUP
   ============================================================ */

window.addEventListener(
    "beforeunload",
    () => {

        if (cameraRunning) {

            try {

                navigator.sendBeacon(
                    `${VIRTUAL_TRYON_API}/stop-camera`
                );

            } catch (error) {

                console.warn(
                    "Could not stop camera:",
                    error
                );
            }
        }
    }
);


/* ============================================================
   GLOBAL FUNCTIONS
   ============================================================ */

window.openVirtualFittingRoom =
    openVirtualFittingRoom;

window.closeVirtualFittingRoom =
    closeVirtualFittingRoom;

window.openCamera =
    openCamera;

window.startVirtualTryOn =
    startVirtualTryOn;

window.changeVirtualClothing =
    changeVirtualClothing;

window.stopCamera =
    stopCamera;

window.uploadPhotoPlaceholder =
    uploadPhotoPlaceholder;


console.log(
    "Virtual Try-On JavaScript loaded."
);
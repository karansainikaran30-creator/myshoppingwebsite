// ============================================================
// MyShop - Main JavaScript
// Step 18.5 - Cart Persistence & User Experience
// CSS Compatible Version
// ============================================================


// ============================================================
// GLOBAL DATA
// ============================================================

let products = [];
let cart = [];

const CART_STORAGE_KEY = "myShopCart";


// ============================================================
// LOAD CART FROM LOCAL STORAGE
// ============================================================

function loadCartFromStorage() {

    try {

        const savedCart =
            localStorage.getItem(CART_STORAGE_KEY);

        if (!savedCart) {

            cart = [];

            return;
        }

        const parsedCart =
            JSON.parse(savedCart);

        if (!Array.isArray(parsedCart)) {

            cart = [];

            return;
        }

        cart = parsedCart
            .map(item => {

                return {
                    id: Number(item.id),
                    name: item.name || "",
                    price: Number(item.price) || 0,
                    image: item.image || "",
                    category: item.category || "",
                    description: item.description || "",
                    stock: Number(item.stock) || 0,
                    quantity: Number(item.quantity) || 0
                };

            })
            .filter(item => {

                return (
                    Number.isInteger(item.id) &&
                    item.id > 0 &&
                    Number.isInteger(item.quantity) &&
                    item.quantity > 0
                );

            });

    }

    catch (error) {

        console.error(
            "CART LOAD ERROR:",
            error
        );

        cart = [];
    }
}


// ============================================================
// SAVE CART TO LOCAL STORAGE
// ============================================================

function saveCartToStorage() {

    try {

        localStorage.setItem(
            CART_STORAGE_KEY,
            JSON.stringify(cart)
        );

    }

    catch (error) {

        console.error(
            "CART SAVE ERROR:",
            error
        );
    }
}


// ============================================================
// UPDATE CART COUNT
// ============================================================

function updateCartCount() {

    const cartCountElement =
        document.getElementById("cartCount");

    if (!cartCountElement) {
        return;
    }

    const totalQuantity =
        cart.reduce(
            (total, item) => {

                return total + Number(item.quantity);

            },
            0
        );

    cartCountElement.textContent =
        totalQuantity;
}


// ============================================================
// LOAD PRODUCTS
// ============================================================

async function loadProducts() {

    try {

        const response =
            await fetch("/api/products");

        if (!response.ok) {

            throw new Error(
                "Failed to load products."
            );
        }

        const databaseProducts =
            await response.json();

        products =
            databaseProducts.map(product => {

                return {
                    ...product,
                    id: Number(product.id),
                    price: Number(product.price),
                    stock: Number(product.stock)
                };

            });


        // Check saved cart against latest database.
        validateCartStock();


        displayProducts(products);

    }

    catch (error) {

        console.error(
            "PRODUCT LOAD ERROR:",
            error
        );

        const container =
            document.getElementById(
                "productContainer"
            );

        if (container) {

            container.innerHTML = `
                <div
                    style="
                        text-align:center;
                        padding:30px;
                    "
                >

                    <h3>
                        Unable to load products.
                    </h3>

                    <p>
                        Please refresh the page.
                    </p>

                </div>
            `;
        }
    }
}


// ============================================================
// VALIDATE CART WITH DATABASE
// ============================================================

function validateCartStock() {

    if (!Array.isArray(cart)) {

        cart = [];

        saveCartToStorage();

        updateCartCount();

        return;
    }


    const validatedCart = [];


    cart.forEach(cartItem => {

        const latestProduct =
            products.find(
                product =>
                    Number(product.id) ===
                    Number(cartItem.id)
            );


        // ----------------------------------------------------
        // PRODUCT DELETED
        // ----------------------------------------------------

        if (!latestProduct) {

            return;
        }


        // ----------------------------------------------------
        // PRODUCT OUT OF STOCK
        // ----------------------------------------------------

        if (
            Number(latestProduct.stock) <= 0
        ) {

            return;
        }


        // ----------------------------------------------------
        // CHECK QUANTITY
        // ----------------------------------------------------

        let quantity =
            Number(cartItem.quantity);


        if (!Number.isInteger(quantity)) {

            quantity = 1;
        }


        if (quantity < 1) {

            quantity = 1;
        }


        // ----------------------------------------------------
        // QUANTITY CANNOT EXCEED STOCK
        // ----------------------------------------------------

        if (
            quantity >
            Number(latestProduct.stock)
        ) {

            quantity =
                Number(latestProduct.stock);
        }


        // ----------------------------------------------------
        // SAVE UPDATED PRODUCT INFORMATION
        // ----------------------------------------------------

        validatedCart.push({

            id:
                Number(latestProduct.id),

            name:
                latestProduct.name,

            price:
                Number(latestProduct.price),

            image:
                latestProduct.image || "",

            category:
                latestProduct.category || "",

            description:
                latestProduct.description || "",

            stock:
                Number(latestProduct.stock),

            quantity:
                quantity

        });

    });


    cart = validatedCart;


    saveCartToStorage();

    updateCartCount();
}


// ============================================================
// DISPLAY PRODUCTS
// ============================================================

function displayProducts(productList) {

    const container =
        document.getElementById(
            "productContainer"
        );

    if (!container) {
        return;
    }


    if (
        !productList ||
        productList.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-message">

                <h3>
                    No products found.
                </h3>

                <p>
                    Try another search or category.
                </p>

            </div>
        `;

        return;
    }


    container.innerHTML =
        productList.map(product => {

            const stock =
                Number(product.stock) || 0;

            const isOutOfStock =
                stock <= 0;


            return `
                <div class="product-card">

                    ${
                        product.image
                        ?
                        `
                        <img
                            src="${product.image}"
                            alt="${product.name}"
                            onclick="openProductDetails(${product.id})"
                            style="cursor:pointer;"
                            onerror="
                                this.style.display='none';
                            "
                        >
                        `
                        :
                        `
                        <div
                            onclick="openProductDetails(${product.id})"
                            style="
                                height:260px;
                                display:flex;
                                align-items:center;
                                justify-content:center;
                                font-size:60px;
                                background:#f5f5f5;
                                cursor:pointer;
                            "
                        >
                            🛍️
                        </div>
                        `
                    }


                    <div class="product-info">

                        <h3>
                            ${product.name}
                        </h3>

                        <p>
                            ${product.category}
                        </p>

                        <p class="product-price">
                            ₹${Number(product.price).toFixed(2)}
                        </p>


                        ${
                            isOutOfStock
                            ?
                            `
                            <p>
                                <strong>
                                    Out of Stock
                                </strong>
                            </p>
                            `
                            :
                            `
                            <p>
                                ${stock} available
                            </p>
                            `
                        }


                        <div class="product-buttons">

                            <button
                                class="view-btn"
                                onclick="openProductDetails(${product.id})"
                            >
                                View Details
                            </button>


                            <button
                                class="add-btn"
                                onclick="addToCart(${product.id})"
                                ${
                                    isOutOfStock
                                    ? "disabled"
                                    : ""
                                }
                            >
                                ${
                                    isOutOfStock
                                    ? "Out of Stock"
                                    : "Add to Cart"
                                }
                            </button>

                        </div>

                    </div>

                </div>
            `;

        }).join("");
}


// ============================================================
// PRODUCT DETAILS
// ============================================================

function openProductDetails(productId) {

    const product =
        products.find(
            item =>
                Number(item.id) ===
                Number(productId)
        );

    if (!product) {
        return;
    }


    const modal =
        document.getElementById(
            "productModal"
        );

    const image =
        document.getElementById(
            "detailImage"
        );

    const name =
        document.getElementById(
            "detailName"
        );

    const price =
        document.getElementById(
            "detailPrice"
        );

    const category =
        document.getElementById(
            "detailCategory"
        );

    const description =
        document.getElementById(
            "detailDescription"
        );

    const addButton =
        document.getElementById(
            "detailAddButton"
        );


    if (image) {

        image.src =
            product.image || "";

        image.alt =
            product.name;
    }


    if (name) {

        name.textContent =
            product.name;
    }


    if (price) {

        price.textContent =
            `₹${Number(product.price).toFixed(2)}`;
    }


    if (category) {

        category.textContent =
            product.category;
    }


    if (description) {

        description.textContent =
            product.description ||
            "No description available.";
    }


    if (addButton) {

        if (
            Number(product.stock) <= 0
        ) {

            addButton.textContent =
                "Out of Stock";

            addButton.disabled =
                true;

        }

        else {

            addButton.textContent =
                "Add to Cart";

            addButton.disabled =
                false;

            addButton.onclick =
                function () {

                    addToCart(
                        product.id
                    );

                };
        }
    }


    if (modal) {

        modal.style.display =
            "flex";
    }
}


// ============================================================
// CLOSE PRODUCT DETAILS
// ============================================================

function closeProductDetails() {

    const modal =
        document.getElementById(
            "productModal"
        );

    if (modal) {

        modal.style.display =
            "none";
    }
}


// ============================================================
// ADD TO CART
// ============================================================

function addToCart(productId) {

    const product =
        products.find(
            item =>
                Number(item.id) ===
                Number(productId)
        );


    if (!product) {

        alert(
            "Product not found."
        );

        return;
    }


    const stock =
        Number(product.stock) || 0;


    if (stock <= 0) {

        alert(
            "This product is out of stock."
        );

        return;
    }


    const existingItem =
        cart.find(
            item =>
                Number(item.id) ===
                Number(product.id)
        );


    if (existingItem) {

        if (
            existingItem.quantity >=
            stock
        ) {

            alert(
                `Only ${stock} items are available.`
            );

            return;
        }


        existingItem.quantity += 1;

        existingItem.stock =
            stock;

        existingItem.price =
            Number(product.price);

        existingItem.name =
            product.name;

        existingItem.image =
            product.image || "";

        existingItem.category =
            product.category || "";

        existingItem.description =
            product.description || "";

    }

    else {

        cart.push({

            id:
                Number(product.id),

            name:
                product.name,

            price:
                Number(product.price),

            image:
                product.image || "",

            category:
                product.category || "",

            description:
                product.description || "",

            stock:
                stock,

            quantity:
                1
        });
    }


    saveCartToStorage();

    updateCartCount();

    showCartMessage(
        `${product.name} added to cart.`
    );
}


// ============================================================
// CART MESSAGE
// ============================================================

function showCartMessage(message) {

    const oldMessage =
        document.getElementById(
            "cartToast"
        );

    if (oldMessage) {

        oldMessage.remove();
    }


    const toast =
        document.createElement(
            "div"
        );

    toast.id =
        "cartToast";

    toast.textContent =
        message;


    // Keep this message independent
    // from existing website CSS.

    toast.style.position =
        "fixed";

    toast.style.bottom =
        "25px";

    toast.style.right =
        "25px";

    toast.style.zIndex =
        "9999";

    toast.style.padding =
        "12px 18px";

    toast.style.background =
        "#16a34a";

    toast.style.color =
        "white";

    toast.style.borderRadius =
        "8px";

    toast.style.fontWeight =
        "bold";

    toast.style.boxShadow =
        "0 5px 20px rgba(0,0,0,0.2)";


    document.body.appendChild(
        toast
    );


    setTimeout(
        function () {

            if (toast) {

                toast.remove();
            }

        },
        2000
    );
}


// ============================================================
// OPEN CART
// ============================================================

function openCart() {

    loadCartFromStorage();

    validateCartStock();

    displayCart();


    const modal =
        document.getElementById(
            "cartModal"
        );

    if (modal) {

        modal.style.display =
            "flex";
    }
}


// ============================================================
// CLOSE CART
// ============================================================

function closeCart() {

    const modal =
        document.getElementById(
            "cartModal"
        );

    if (modal) {

        modal.style.display =
            "none";
    }
}


// ============================================================
// DISPLAY CART
// ============================================================

function displayCart() {

    const container =
        document.getElementById(
            "cartItems"
        );

    const totalElement =
        document.getElementById(
            "cartTotal"
        );


    if (!container) {
        return;
    }


    if (
        !cart ||
        cart.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-cart">

                <h3>
                    Your cart is empty 🛒
                </h3>

                <p>
                    Add some products to continue shopping.
                </p>

            </div>
        `;


        if (totalElement) {

            totalElement.textContent =
                "0.00";
        }


        updateCartCount();

        return;
    }


    let total = 0;


    container.innerHTML =
        cart.map(item => {

            const quantity =
                Number(item.quantity);

            const price =
                Number(item.price);

            const subtotal =
                price * quantity;


            total += subtotal;


            return `
                <div class="cart-item">


                    ${
                        item.image
                        ?
                        `
                        <img
                            src="${item.image}"
                            alt="${item.name}"
                            onerror="
                                this.style.display='none';
                            "
                        >
                        `
                        :
                        `
                        <div
                            style="
                                width:80px;
                                height:80px;
                                display:flex;
                                align-items:center;
                                justify-content:center;
                                background:#f5f5f5;
                                border-radius:12px;
                                font-size:35px;
                            "
                        >
                            🛍️
                        </div>
                        `
                    }


                    <div class="cart-item-info">

                        <h3>
                            ${item.name}
                        </h3>

                        <p>
                            ₹${price.toFixed(2)}
                        </p>

                        <p class="cart-subtotal">

                            <strong>
                                Subtotal:
                            </strong>

                            ₹${subtotal.toFixed(2)}

                        </p>

                    </div>


                    <div class="quantity-controls">

                        <button
                            onclick="changeQuantity(${item.id}, -1)"
                            aria-label="Decrease quantity"
                        >
                            −
                        </button>


                        <span class="quantity-number">
                            ${quantity}
                        </span>


                        <button
                            onclick="changeQuantity(${item.id}, 1)"
                            ${
                                quantity >=
                                Number(item.stock)
                                ? "disabled"
                                : ""
                            }
                            aria-label="Increase quantity"
                        >
                            +
                        </button>

                    </div>


                    <button
                        class="remove-btn"
                        onclick="removeFromCart(${item.id})"
                    >
                        Remove
                    </button>


                </div>
            `;

        }).join("");


    if (totalElement) {

        totalElement.textContent =
            total.toFixed(2);
    }


    updateCartCount();
}


// ============================================================
// CHANGE CART QUANTITY
// ============================================================

function changeQuantity(
    productId,
    change
) {

    const item =
        cart.find(
            cartItem =>
                Number(cartItem.id) ===
                Number(productId)
        );


    if (!item) {
        return;
    }


    const latestProduct =
        products.find(
            product =>
                Number(product.id) ===
                Number(productId)
        );


    if (!latestProduct) {

        removeFromCart(
            productId
        );

        return;
    }


    const stock =
        Number(latestProduct.stock) || 0;


    if (stock <= 0) {

        removeFromCart(
            productId
        );

        return;
    }


    const newQuantity =
        Number(item.quantity) +
        Number(change);


    // --------------------------------------------------------
    // REMOVE WHEN QUANTITY BECOMES ZERO
    // --------------------------------------------------------

    if (newQuantity <= 0) {

        removeFromCart(
            productId
        );

        return;
    }


    // --------------------------------------------------------
    // STOCK LIMIT
    // --------------------------------------------------------

    if (
        newQuantity >
        stock
    ) {

        alert(
            `Only ${stock} items are available.`
        );

        return;
    }


    item.quantity =
        newQuantity;

    item.stock =
        stock;

    item.price =
        Number(latestProduct.price);

    item.name =
        latestProduct.name;

    item.image =
        latestProduct.image || "";

    item.category =
        latestProduct.category || "";

    item.description =
        latestProduct.description || "";


    saveCartToStorage();

    updateCartCount();

    displayCart();
}


// ============================================================
// REMOVE PRODUCT FROM CART
// ============================================================

function removeFromCart(productId) {

    cart =
        cart.filter(
            item =>
                Number(item.id) !==
                Number(productId)
        );


    saveCartToStorage();

    updateCartCount();

    displayCart();
}


// ============================================================
// SEARCH PRODUCTS
// ============================================================

function searchProducts() {

    const input =
        document.getElementById(
            "searchInput"
        );


    if (!input) {
        return;
    }


    const searchText =
        input.value
            .trim()
            .toLowerCase();


    if (!searchText) {

        displayProducts(
            products
        );

        return;
    }


    const filteredProducts =
        products.filter(
            product => {

                const name =
                    String(
                        product.name || ""
                    ).toLowerCase();


                const category =
                    String(
                        product.category || ""
                    ).toLowerCase();


                const description =
                    String(
                        product.description || ""
                    ).toLowerCase();


                return (
                    name.includes(searchText) ||
                    category.includes(searchText) ||
                    description.includes(searchText)
                );

            }
        );


    displayProducts(
        filteredProducts
    );
}


// ============================================================
// CATEGORY FILTER
// ============================================================

function filterCategory(category) {

    const filteredProducts =
        products.filter(
            product => {

                return (
                    String(
                        product.category || ""
                    ).toLowerCase() ===
                    String(
                        category
                    ).toLowerCase()
                );

            }
        );


    displayProducts(
        filteredProducts
    );


    const productsSection =
        document.getElementById(
            "products"
        );


    if (productsSection) {

        productsSection.scrollIntoView({
            behavior: "smooth"
        });
    }
}


// ============================================================
// SCROLL TO PRODUCTS
// ============================================================

function scrollToProducts() {

    const section =
        document.getElementById(
            "products"
        );


    if (section) {

        section.scrollIntoView({
            behavior: "smooth"
        });
    }
}


// ============================================================
// GO TO CHECKOUT
// ============================================================

function goToCheckout() {

    loadCartFromStorage();


    if (
        !cart ||
        cart.length === 0
    ) {

        alert(
            "Your cart is empty."
        );

        return;
    }


    // Check latest known stock.

    validateCartStock();


    if (
        !cart ||
        cart.length === 0
    ) {

        alert(
            "Your cart is empty or some products are no longer available."
        );

        return;
    }


    saveCartToStorage();

    updateCartCount();


    // IMPORTANT:
    // DO NOT clear cart here.
    // Cart will be cleared only after
    // successful order placement.

    window.location.href =
        "/checkout";
}


// ============================================================
// CHECKOUT PAGE STOCK CHECK
// ============================================================

async function loadCheckout() {

    const checkoutContainer =
        document.getElementById(
            "checkoutContainer"
        );


    if (!checkoutContainer) {
        return;
    }


    loadCartFromStorage();


    if (
        !cart ||
        cart.length === 0
    ) {

        return;
    }


    try {

        const response =
            await fetch(
                "/api/products"
            );


        if (!response.ok) {

            throw new Error(
                "Unable to verify stock."
            );
        }


        const databaseProducts =
            await response.json();


        products =
            databaseProducts.map(
                product => {

                    return {
                        ...product,
                        id: Number(product.id),
                        price: Number(product.price),
                        stock: Number(product.stock)
                    };

                }
            );


        validateCartStock();

    }

    catch (error) {

        console.error(
            "CHECKOUT STOCK ERROR:",
            error
        );

        console.log(
            "Using saved cart data."
        );
    }
}


// ============================================================
// MODAL OUTSIDE CLICK
// ============================================================

window.addEventListener(
    "click",
    function (event) {

        const productModal =
            document.getElementById(
                "productModal"
            );


        const cartModal =
            document.getElementById(
                "cartModal"
            );


        if (
            productModal &&
            event.target === productModal
        ) {

            closeProductDetails();
        }


        if (
            cartModal &&
            event.target === cartModal
        ) {

            closeCart();
        }

    }
);


// ============================================================
// MULTI-TAB CART SYNC
// ============================================================

window.addEventListener(
    "storage",
    function (event) {

        if (
            event.key !==
            CART_STORAGE_KEY
        ) {

            return;
        }


        loadCartFromStorage();

        updateCartCount();


        const cartModal =
            document.getElementById(
                "cartModal"
            );


        if (
            cartModal &&
            cartModal.style.display === "flex"
        ) {

            displayCart();
        }

    }
);


// ============================================================
// PAGE LOAD
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        // ----------------------------------------------------
        // LOAD SAVED CART
        // ----------------------------------------------------

        loadCartFromStorage();

        updateCartCount();


        // ----------------------------------------------------
        // HOME PAGE
        // ----------------------------------------------------

        const productContainer =
            document.getElementById(
                "productContainer"
            );


        if (productContainer) {

            loadProducts();
        }


        // ----------------------------------------------------
        // CHECKOUT PAGE
        // ----------------------------------------------------

        const checkoutContainer =
            document.getElementById(
                "checkoutContainer"
            );


        if (checkoutContainer) {

            loadCheckout();
        }

    }
);
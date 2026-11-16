let selected_product = null;
let current_user = null;
let access_token = null;
let products = [];
let saved_records = [];
console.log("app.js terhubung")
function showToast(message,type="info"){
    const container = document.getElementById("toast-container");
    if (!container){
        console.error("Toast container not found)");
        return;
    }
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const icon = document.createElement("span");
    icon.className = "toast-icon";
    if (type === "success"){
        icon.textContent = "✓"
    } else if (type === "error"){
        icon.textContent = "✗"
    } else {
        icon.textContent = "ⓘ"
    }
    const text = document.createElement("span")
    text.className = "toast-message"
    text.textContent = message;
    const closeButton = document.createElement("button");
    closeButton.className = "toast-close";
    closeButton.textContent = "x";
    closeButton.setAttribute("aria-label", "close notification");
    toast.setAttribute("role", type==="error" ? "alert" : "status");
    toast.appendChild(icon);
    toast.appendChild(text);
    toast.appendChild(closeButton);
    container.appendChild(toast);
    let isCLosing = false;
    function removeToast(){
        if (isCLosing){
            return;
        }
        isCLosing = true;
        toast.remove();
    }
    closeButton.addEventListener("click", removeToast);
    setTimeout(removeToast, 3000);
}
async function api_request(path, options={}){
    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };
    if (access_token){
        headers["Authorization"] = `Bearer ${access_token}`;
    }
    const response = await fetch(path,{
        ...options, headers: headers
    });
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
        throw new Error(`Server returned HTTP ${response.status} instead of JSON.`);
    }
    const data = await response.json();
    if (!response.ok){
        throw new Error(data.error || `Request failed: HTTP ${response.status}`);
    }
    return data;
}
function format_price(price, transaction_type){
    const formatted = Number(price).toLocaleString("id-ID");
    if (transaction_type === "rental"){
        return `Rp${formatted}/day`;
    }
    return `Rp${formatted}`;
}
function render_products(items){
    const container = document.getElementById("products-container");
    container.replaceChildren();
    if (items.length === 0){
        const message = document.createElement("p")
        message.className = "empty-message";
        message.textContent = "No product found."
        container.appendChild(message);
        return;
    }
    items.forEach(item => {
        const card = document.createElement("div");
        card.className = "product";
        const imageBox = document.createElement("div");
        imageBox.className = "product-image";
        const image = document.createElement("img");
        image.src = item.image_url;
        image.alt = item.name;
        const badge = document.createElement("span");
        badge.className = "product-badge " + item.transaction_type;
        badge.textContent = item.transaction_type === "rental"
            ? "Rental"
            : "Secondhand";
        imageBox.appendChild(image);
        imageBox.appendChild(badge);
        const info = document.createElement("div");
        info.className = "product-info";
        const name = document.createElement("h3");
        name.textContent = item.name;
        const price = document.createElement("h4");
        price.textContent = format_price(item.price,item.transaction_type);
        info.appendChild(name);
        info.appendChild(price);
        card.appendChild(imageBox);
        card.appendChild(info);
        card.addEventListener("click", () => {open_product(item.id);})
        container.appendChild(card);
    })
}
let latest_search_request = 0;
async function load_items(search=""){
    const request_id = ++latest_search_request;
    const container = document.getElementById("products-container");
    try{
        const data = await api_request(`/items?search=${encodeURIComponent(search)}`);
        if (request_id !== latest_search_request){
            return;
        }
        products = data.items;
        render_products(products);
    } catch (error) {
        if (request_id !== latest_search_request){
            return;
        }
        container.replaceChildren();
        const message = document.createElement("p")
        message.className = "empty-message";
        message.textContent = "Failed to load product: " + error.message;
        container.appendChild(message);
    }
}
const searchInput = document.getElementById("search-input");
let search_timer;
searchInput.addEventListener("input", function(){
    clearTimeout(search_timer);
    search_timer = setTimeout(()=>{
        load_items(searchInput.value);
    },300);
});
async function open_product(itemId) {
    try {
        const data = await api_request(`/items/${itemId}`);
        selected_product = data.item;
        document.getElementById("modal-name").textContent = selected_product.name;
        document.getElementById("modal-price").textContent = format_price(selected_product.price, selected_product.transaction_type);
        document.getElementById("modal-image").src = selected_product.image_url;
        document.getElementById("modal-condition").textContent = selected_product.condition;
        document.getElementById("modal-description").textContent = selected_product.description;
        document.getElementById("modal-seller").textContent = selected_product.seller;
        const type = document.getElementById("modal-type");

        type.textContent =
            selected_product.transaction_type === "rental"
                ? "Rental"
                : "Secondhand";
        type.className =
            "product-badge " + selected_product.transaction_type;
        document.getElementById("product-modal").classList.remove("hidden");
    } catch (error) {
        showToast(error.message, "error");
    }
}
async function register(event){
        event.preventDefault();
        const name = document.getElementById("register-name").value.trim();
        const email = document.getElementById("register-email").value.trim();
        const password = document.getElementById("register-password").value;
        const role = document.getElementById("register-role").value;
        try{
            const data = await api_request(`/register`, {
                method: "POST",
                body: JSON.stringify({
                    name: name,
                    email: email,
                    password: password,
                    role: role,
                })
            })
            showToast(data.message, "success");
            event.target.reset();
            show_page("login")
        } catch (error){
            showToast(error.message,"error");
        }
}
async function login(event){
    event.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    try{
        const data = await api_request(`/login`, {
            method: "POST",
            body: JSON.stringify({
                email: email,
                password: password,
            })
        });
        access_token = data.access_token;
        current_user = data.user;
        event.target.reset();
        updateNavbar();
        showToast("Login successful!", "success");
        if (current_user.role === "merchant"){
            await show_page("merchant");
        }else{
            await show_page("explore");
        }
    } catch (error){
        showToast(error.message, "error");
    }
}
function updateNavbar() {
    const loginButton = document.querySelector(".login-btn");
    const registerButton = document.querySelector(".register-btn");
    const logoutButton = document.getElementById("logout-btn");
    const merchantButton = document.getElementById("merchant-btn");
    const buyerButtons = document.querySelectorAll('.nav-icon:not(#merchant-btn)');
    const loggedIn = current_user !== null;

    const isBuyer = loggedIn && current_user.role === "buyer";
    const isMerchant = loggedIn && current_user.role === "merchant";
    loginButton.classList.toggle("hidden", loggedIn);
    registerButton.classList.toggle("hidden", loggedIn);
    logoutButton.classList.toggle("hidden", !loggedIn);

    merchantButton.classList.toggle("hidden", !isMerchant);
    buyerButtons.forEach(button => {button.classList.toggle("hidden",!isBuyer)})
}
function logout() {
    access_token = null;
    current_user = null;
    selected_product = null;
    saved_records = [];
    updateNavbar();
    show_page("home");
}
async function show_page(page){
    if (page === "wishlist" || page === "cart"){
        if (!current_user) {
            showToast("You are not logged in!", "error");
            page = "login";
        } else if (current_user.role !== "buyer"){
            showToast("You are not logged in as buyer!", "error");
            return;
        }
    }

    if (page === "merchant"){
        if (!current_user) {
            showToast("You are not logged in!", "error");
            page = "login";
        }else if (current_user.role !== "merchant"){
            showToast("You are not logged in as buyer!", "error");
            return;
        }
    }
    document.querySelectorAll(".page").forEach(item => {item.classList.add("hidden")});
    document.getElementById(page).classList.remove("hidden");
    window.scrollTo(0,0);
    if (page === "explore"){
        await load_items(document.getElementById("search-input").value);
    }
    if (page==="wishlist" || page==="cart"){
        try{
            await load_saved_items();
        } catch (error) {
            showToast("Failed to load items: " + error.message, "error");
        }

    }
    if (page === "merchant") {
        await load_merchant_products();
    }
}
async function load_saved_items(){
    if (!current_user || current_user.role !== "buyer") {
        return;
    }
    const data = await api_request(`/user-items`);
    saved_records = data.user_items;
    renderSavedItems();
}
async function add_saved_items(status){
    if (!current_user){
        closeModal();
        showToast("You are not logged in!","error");
        show_page("login");
        return;
    }
    if (current_user.role !== "buyer"){
        showToast("You are not logged in as buyer!","error");
        return;
    }
    if(!selected_product){
        return;
    }
    try{
        await load_saved_items();
        const existing = saved_records.find(record => record.item_id === selected_product.id);
        if(existing){
            if (existing.status === status){
                showToast("Product is already in this list.", "info");
                return;
            }
            await api_request(`/user-items/${existing.id}`, {
                method: "PATCH",
                body: JSON.stringify({status:status}),
            });
        } else {
            await api_request(`/user-items`, {
                method: "POST",
                body: JSON.stringify({item_id:selected_product.id, status: status}),
            });
        }
        await load_saved_items();
        closeModal();
        showToast(
    status === "cart"
                ? "Product added to cart!"
                : "Product added to wishlist!", "success"
        );
    } catch(error){
        showToast(error.message, "error");

    }
}
async function addWishlist(){
    await add_saved_items("wishlist");
}
async function addCart(){
    await add_saved_items("cart");
}
function create_saved_items(record){
    const item=document.createElement("div");
    item.className = "saved-item";
    const image = document.createElement("img");
    image.src = record.product.image_url;
    image.alt = record.product.name;
    const info = document.createElement("div");
    const name = document.createElement("h3");
    name.textContent = record.product.name;
    const price = document.createElement("p");
    price.textContent = format_price(record.product.price, record.product.transaction_type);
    info.appendChild(name);
    info.appendChild(price);

    const button = document.createElement("button");
    button.textContent = "Remove"
    button.addEventListener("click", ()=>{removeItem(record.id)});
    item.appendChild(image)
    item.appendChild(info)
    item.appendChild(button)
    return item;
}
function create_cart_item(record){
    const product = record.product;
    const item = document.createElement("div");
    item.className = "cart-summary-item";
    const image = document.createElement("img");
    image.src = product.image_url;
    image.alt = product.name;
    image.className = "cart-summary-image";
    const info = document.createElement("div");
    info.className = "cart-summary-info";
    const name = document.createElement("h3");
    name.textContent = product.name;
    const details = document.createElement("p");
    details.className = "cart-summary-details";
    const transaction_label =product.transaction_type === "rental"
        ? "Rental"
        : "Secondhand";
    details.textContent = `${transaction_label} · ${product.condition}`;
    const price = document.createElement("h4");
    price.className = "cart-summary-price";
    price.textContent = format_price(product.price, product.transaction_type);
    const seller = document.createElement("p");
    seller.className = "cart-summary-seller";
    seller.textContent = `Merchant: ${product.seller}`;

    const email = document.createElement("a");
    email.className = "cart-summary-email";
    email.textContent = product.seller_email;
    const subject = `Question about ${product.name} in CampusCycle`
    email.href =
        `mailto:${encodeURIComponent(product.seller_email)}` +
        `?subject=${encodeURIComponent(subject)}`;
    const removeButton = document.createElement("button");
    removeButton.className = "cart-remove-btn";
    removeButton.textContent = "Remove";
    removeButton.addEventListener("click", ()=>{removeItem(record.id)});

    info.appendChild(name);
    info.appendChild(details);
    info.appendChild(price);
    info.appendChild(seller);
    info.appendChild(email);

    item.appendChild(image);
    item.appendChild(info);
    item.appendChild(removeButton);
    return item;

}
function renderSavedItems(){
    const wishlist_box = document.getElementById("wishlist-items");
    const cart_box = document.getElementById("cart-items");
    wishlist_box.replaceChildren();
    cart_box.replaceChildren();
    const wishlist = saved_records.filter(record => record.status === "wishlist");
    const cart = saved_records.filter(record => record.status === "cart");
    wishlist.forEach(record => {wishlist_box.appendChild(create_saved_items(record))});
    cart.forEach(record => {cart_box.appendChild(create_cart_item(record))});
    if (wishlist.length === 0){
        const message = document.createElement("p");
        message.className = "empty-message";
        message.textContent = "Wishlist is empty!";
        wishlist_box.appendChild(message);
    }
    if (cart.length === 0){
        const message = document.createElement("p");
        message.className = "empty-message";
        message.textContent = "Cart is empty!";
        cart_box.appendChild(message);
    }
    const total = cart.reduce((sum,record)=>{
        return sum + Number(record.product.price);
    }, 0);
    document.getElementById("cart-total").textContent = "Rp" + total.toLocaleString("id-ID");
}
async function removeItem(recordId){
    try{
        await api_request(`/user-items/${recordId}`,{method: "DELETE"})
        await load_saved_items();
    }catch (error) {
        showToast(error.message, "error");
    }
}
function closeModal() {
    document.getElementById('product-modal').classList.add('hidden');
}
async function addNewProduct(event){
    event.preventDefault();
    if (!current_user || current_user.role !== "merchant"){
        showToast("Merchant access is required!", "error")
        return;
    }
    const name = document.getElementById("new-name").value.trim();
    const price = document.getElementById("new-price").value;
    const transaction_type = document.querySelector('input[name="new-type"]:checked').value;
    const condition = document.getElementById("new-condition").value;
    const image_url = document.getElementById("new-image").value.trim();
    const description = document.getElementById("new-description").value.trim();

    const submitButton = event.target.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    try{
        const data = await api_request(`/items`, {
            method: "POST",
            body: JSON.stringify({
                name:name,
                price:price,
                transaction_type:transaction_type,
                condition:condition,
                image_url:image_url,
                description:description
            })
        });
        showToast("Product added successfully!", "success");
        event.target.reset();
        await show_page("explore");
    } catch (error) {
        showToast("Failed to add product: " + error.message, "error");
    } finally {
        submitButton.disabled = false;
    }
}
async function load_merchant_products(){
    const container = document.getElementById("merchant-products-list");
    try{
        const data = await api_request(`/merchant/items`);
        container.replaceChildren();
        if(data.items.length === 0){
            const message = document.createElement("p");
            message.className = "empty-message";
            message.textContent = "You have no products yet.";
            container.appendChild(message);
            return;
        }
        data.items.forEach(product => {
            const card = document.createElement("div");
            card.className = "merchant-product-item";
            const image = document.createElement("img");
            image.src = product.image_url;
            image.alt = product.name;
            const info = document.createElement("div")
            info.className = "merchant-product-info";
            const name = document.createElement("h4");
            name.textContent = product.name;
            const price = document.createElement("p");
            price.textContent = format_price(product.price, product.transaction_type);
            const deleteButton = document.createElement("button");
            deleteButton.className = "delete-product-btn";
            deleteButton.textContent = "Delete";
            deleteButton.addEventListener("click", ()=>{
                delete_merchant_product(product.id);
            });
            info.appendChild(name);
            info.appendChild(price);

            card.appendChild(image);
            card.appendChild(info);
            card.appendChild(deleteButton);
            container.appendChild(card);
        })
    } catch (error) {
        showToast("Failed to load your products: " + error.message, "error");
    }
}
async function delete_merchant_product(itemId){
    const confirmed = confirm("Are you sure you want to delete?");
    if (!confirmed){
        return;
    }
    try{
        const data = await api_request(`/items/${itemId}`, {method: "DELETE"});
        showToast("Product deleted successfully!", "success");
        await load_merchant_products();
    } catch (error){
        showToast("Failed to delete product: " + error.message, "error");
    }
}
updateNavbar()
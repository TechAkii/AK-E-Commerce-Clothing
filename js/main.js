let currentProducts = [...products];

document.addEventListener("DOMContentLoaded", () => {
    renderProducts();
    updateCartUI();
    document.querySelectorAll("#wishlistCount").forEach(e => e.textContent = wishlist.length);
    document.querySelectorAll(".filter-chip").forEach(b => b.addEventListener("click", () => {
        document.querySelectorAll(".filter-chip").forEach(x => x.classList.remove("active"));
        b.classList.add("active");
        currentProducts = products.filter(p => b.dataset.filter === "All" || p.category === b.dataset.filter);
        renderProducts(currentProducts);
    }));
    const params = new URLSearchParams(location.search);
    if (document.getElementById("productPage")) return;
    if (params.get("category")) applyCategoryFromURL(params.get("category"));
    if (params.get("new") === "true") {
        currentProducts = products.filter(p => p.new);
        renderProducts(currentProducts);
    }
});

function productCard(p) {
    const wished = wishlist.includes(p.id);
    return `<article class="product-card"><div class="product-image"><a href="product.html?id=${p.id}"><img src="${p.image}" alt="${p.name}"><img class="alt-image" src="${p.alt}" alt="${p.name} alternate view"></a>${p.new?'<span class="badge">NEW</span>':""}<button class="heart ${wished?"liked":""}" onclick="toggleWishlist(${p.id})">${wished?"♥":"♡"}</button><button class="tryon-mini" onclick='openVirtualFittingRoom(${JSON.stringify(p).replace(/'/g,"&#39;")})'>Try It Virtually</button></div><div class="product-meta"><div><p class="product-cat">${p.category}</p><h3>${p.name}</h3></div><strong>$${p.price.toFixed(2)}</strong></div><div class="swatches">${p.colors.map(c=>`<i title="${c}" class="swatch ${c.toLowerCase()}"></i>`).join("")}</div><div class="product-actions"><button class="btn btn-dark small" onclick="addToCart(${p.id})">Add to Bag</button><button class="btn btn-outline small" onclick="viewProduct(${p.id})">View Details</button></div></article>`;
}
function renderProducts(list=currentProducts){
 const grid=document.getElementById("productGrid"); if(!grid)return;
 grid.innerHTML=list.length?list.map(productCard).join(""):`<div class="no-results">No pieces match your filters.</div>`;
 const count=document.getElementById("resultCount");if(count)count.textContent=`${list.length} pieces`;
}
function sortProducts(value){
 const list=[...currentProducts]; if(value==="low")list.sort((a,b)=>a.price-b.price);if(value==="high")list.sort((a,b)=>b.price-a.price);if(value==="newest")list.sort((a,b)=>Number(b.new)-Number(a.new));renderProducts(list);
}
function applyCategoryFromURL(cat){currentProducts=products.filter(p=>p.category.toLowerCase()===cat.toLowerCase());renderProducts(currentProducts);}
function initShopPage(){
 const params=new URLSearchParams(location.search); const cat=params.get("category"); if(cat){document.getElementById("categoryFilter").value=cat;}
 ["categoryFilter","sizeFilter","colorFilter","priceFilter","newFilter"].forEach(id=>document.getElementById(id)?.addEventListener("change",applyShopFilters));
 document.getElementById("shopSort")?.addEventListener("change",e=>sortProducts(e.target.value)); applyShopFilters();
}
function applyShopFilters(){
 let list=[...products],cat=document.getElementById("categoryFilter")?.value,size=document.getElementById("sizeFilter")?.value,color=document.getElementById("colorFilter")?.value,price=document.getElementById("priceFilter")?.value;
 if(cat&&cat!=="All")list=list.filter(p=>p.category===cat);if(size&&size!=="All")list=list.filter(p=>p.sizes.includes(size));if(color&&color!=="All")list=list.filter(p=>p.colors.includes(color));if(price&&price!=="All"){const [a,b]=price.split("-").map(Number);list=list.filter(p=>p.price>=a&&p.price<=b);}if(document.getElementById("newFilter")?.checked)list=list.filter(p=>p.new);
 currentProducts=list;renderProducts(list);
}
function viewProduct(id){location.href=`product.html?id=${id}`;}
function renderProductPage(){
 const id=Number(new URLSearchParams(location.search).get("id"))||1,p=products.find(x=>x.id===id)||products[0],box=document.getElementById("productPage");window.activeProduct=p;
 box.innerHTML=`<div class="detail-gallery"><img src="${p.image}" alt="${p.name}"><img src="${p.alt}" alt="${p.name} alternate"></div><div class="detail-info"><p class="eyebrow">${p.category} / ${p.new?"NEW ARRIVAL":"ESSENTIAL"}</p><h1>${p.name}</h1><div class="detail-price">$${p.price.toFixed(2)}</div><p>${p.description}</p><div class="detail-option"><label>Color</label><div class="color-options">${p.colors.map(c=>`<button class="color-option ${c===p.colors[0]?"selected":""}" onclick="selectOption(this)">${c}</button>`).join("")}</div></div><div class="detail-option"><label>Size <button class="find-size" onclick="openSizeModal()">Find My Size</button></label><div class="size-options">${p.sizes.map(s=>`<button class="size-option ${s===p.sizes[1]?"selected":""}" onclick="selectOption(this)">${s}</button>`).join("")}</div></div><div class="detail-option"><label>Quantity</label><div class="quantity-selector"><button onclick="adjustDetailQty(-1)">−</button><span id="detailQty">1</span><button onclick="adjustDetailQty(1)">+</button></div></div><div class="detail-actions"><button class="btn btn-dark full" onclick="addDetailToCart()">Add to Bag</button><button class="btn btn-outline full" onclick='toggleWishlist(${p.id})'>♡ Add to Wishlist</button><button class="btn btn-feature full" onclick='openVirtualFittingRoom(${JSON.stringify(p).replace(/'/g,"&#39;")})'>✦ Try It Virtually</button></div><div class="accordion"><details open><summary>Product Details</summary><p>Designed for everyday wear with considered proportions and premium finishing.</p></details><details><summary>Shipping & Returns</summary><p>Standard delivery and easy returns are available. Connect your preferred commerce backend for live policies.</p></details></div></div>`;
}
function selectOption(el){el.parentElement.querySelectorAll("button").forEach(b=>b.classList.remove("selected"));el.classList.add("selected");}
function adjustDetailQty(d){const e=document.getElementById("detailQty");if(e)e.textContent=Math.max(1,Number(e.textContent)+d);}
function addDetailToCart(){const p=window.activeProduct, size=document.querySelector(".size-option.selected")?.textContent,color=document.querySelector(".color-option.selected")?.textContent,qty=Number(document.getElementById("detailQty")?.textContent)||1;addToCart(p.id,size,color,qty);}
function openSearch(){document.getElementById("searchModal")?.classList.add("show");document.getElementById("overlay")?.classList.add("show");setTimeout(()=>document.getElementById("searchInput")?.focus(),100);}
function closeSearch(){document.getElementById("searchModal")?.classList.remove("show");document.getElementById("overlay")?.classList.remove("show");}
function searchProducts(q){const box=document.getElementById("searchResults");if(!box)return;const term=q.trim().toLowerCase();if(!term){box.innerHTML="<p class='muted'>Start typing to search the collection.</p>";return}const hits=products.filter(p=>(p.name+" "+p.category+" "+p.colors.join(" ")).toLowerCase().includes(term));box.innerHTML=hits.length?hits.map(p=>`<a class="search-result" href="product.html?id=${p.id}"><img src="${p.image}" alt=""><div><strong>${p.name}</strong><small>${p.category} · $${p.price}</small></div></a>`).join(""):"<p class='muted'>No products found.</p>";}
function openSizeModal(){document.getElementById("sizeModal")?.classList.add("show");document.getElementById("overlay")?.classList.add("show");}
function closeSizeModal(){document.getElementById("sizeModal")?.classList.remove("show");document.getElementById("overlay")?.classList.remove("show");}
function closeProduct(){document.getElementById("productModal")?.classList.remove("show");document.getElementById("overlay")?.classList.remove("show");}
function closeAllOverlays(){closeCart();closeSearch();closeSizeModal();closeVirtualFittingRoom();document.getElementById("productModal")?.classList.remove("show");}
function toggleMenu(){document.getElementById("mobileMenu")?.classList.toggle("open");}
function toast(msg){const t=document.getElementById("toast");if(!t)return;t.textContent=msg;t.classList.add("show");clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>t.classList.remove("show"),2600);}
function subscribe(e){e.preventDefault();toast("You're on the list — welcome to My Brand.");e.target.reset();}
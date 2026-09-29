let cart = JSON.parse(localStorage.getItem("mybrand_cart") || "[]");
let wishlist = JSON.parse(localStorage.getItem("mybrand_wishlist") || "[]");

function saveCart(){localStorage.setItem("mybrand_cart",JSON.stringify(cart));updateCartUI();}
function addToCart(id,size=null,color=null,qty=1){
 const p=products.find(x=>x.id===id); if(!p)return;
 size=size||p.sizes[Math.min(1,p.sizes.length-1)]; color=color||p.colors[0];
 const key=`${id}-${size}-${color}`; const item=cart.find(x=>x.key===key);
 if(item)item.qty+=qty; else cart.push({key,id,size,color,qty,price:p.price});
 saveCart(); toast(`${p.name} added to your bag`); openCart();
}
function changeQty(key,delta){const i=cart.find(x=>x.key===key);if(!i)return;i.qty+=delta;if(i.qty<=0)cart=cart.filter(x=>x.key!==key);saveCart();}
function removeFromCart(key){cart=cart.filter(x=>x.key!==key);saveCart();}
function updateCartUI(){
 const total=cart.reduce((s,x)=>s+x.qty,0), subtotal=cart.reduce((s,x)=>s+x.price*x.qty,0);
 document.querySelectorAll("#cartCount").forEach(e=>e.textContent=total);
 document.querySelectorAll("#cartSubtotal").forEach(e=>e.textContent=`$${subtotal.toFixed(2)}`);
 const box=document.getElementById("cartItems"); if(!box)return;
 box.innerHTML=cart.length?cart.map(x=>{const p=products.find(p=>p.id===x.id);return `<div class="cart-item"><img src="${p.image}" alt="${p.name}"><div class="cart-info"><strong>${p.name}</strong><small>${x.size} · ${x.color}</small><div class="qty"><button onclick="changeQty('${x.key}',-1)">−</button><span>${x.qty}</span><button onclick="changeQty('${x.key}',1)">+</button><button class="remove" onclick="removeFromCart('${x.key}')">Remove</button></div><b>$${(x.price*x.qty).toFixed(2)}</b></div></div>`}).join(""):`<div class="empty-state"><span>▢</span><p>Your bag is empty.</p><a class="text-link" href="shop.html">Continue shopping →</a></div>`;
}
function toggleWishlist(id){
 if(wishlist.includes(id))wishlist=wishlist.filter(x=>x!==id);else wishlist.push(id);
 localStorage.setItem("mybrand_wishlist",JSON.stringify(wishlist));renderProducts();updateCartUI();document.querySelectorAll("#wishlistCount").forEach(e=>e.textContent=wishlist.length);toast(wishlist.includes(id)?"Added to wishlist":"Removed from wishlist");
}
function openWishlist(){toast(wishlist.length?`${wishlist.length} item${wishlist.length>1?"s":""} in your wishlist`:"Your wishlist is empty");}
function openCart(){document.getElementById("cartDrawer")?.classList.add("open");document.getElementById("overlay")?.classList.add("show");updateCartUI();}
function closeCart(){document.getElementById("cartDrawer")?.classList.remove("open");document.getElementById("overlay")?.classList.remove("show");}
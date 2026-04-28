/* main.js — ECommerce Dashboard (viva-fixed version) */

const API = '';
let allProducts = [], allOrders = [], orderItems = [];
let logInterval = null, logPaused = false;

// ── Navigation ────────────────────────────────────────────────
const pages    = document.querySelectorAll('.page');
const navItems = document.querySelectorAll('.nav-item[data-page]');

function showPage(id) {
  pages.forEach(p => p.classList.toggle('active', p.id === id));
  navItems.forEach(n => n.classList.toggle('active', n.dataset.page === id));
  document.querySelector('.topbar-title').textContent =
    document.querySelector(`.nav-item[data-page="${id}"]`)?.textContent.trim() || '';
  clearInterval(logInterval);
  switch (id) {
    case 'pg-dashboard': loadDashboard(); setTimeout(loadRecentOrders, 500); break;
    case 'pg-products':  loadProducts();  break;
    case 'pg-orders':    loadOrders();    break;
    case 'pg-users':     loadUsers();     break;
    case 'pg-datafiles': loadDataFiles(); break;
    case 'pg-logs':      startLiveLogs(); break;
  }
}
navItems.forEach(n => n.addEventListener('click', () => showPage(n.dataset.page)));

// ── Toast ─────────────────────────────────────────────────────
function toast(msg, type = 'success') {
  const tc = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast${type === 'error' ? ' error' : type === 'warn' ? ' warn' : ''}`;
  el.innerHTML = `<span>${type==='error'?'❌':type==='warn'?'⚠️':'✅'}</span><span>${msg}</span>`;
  tc.appendChild(el);
  setTimeout(() => { el.style.animation='fadeOut .3s ease forwards'; setTimeout(()=>el.remove(),300); }, 3500);
}

// ── API helper ────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const r = await fetch(API + path, { headers: {'Content-Type':'application/json'}, ...opts });
  const d = await r.json();
  if (!r.ok) throw new Error(d.message || 'API error');
  return d;
}

// ── Modal ─────────────────────────────────────────────────────
function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
document.querySelectorAll('.modal-close,.modal-cancel').forEach(b =>
  b.addEventListener('click', () => closeModal(b.closest('.modal-overlay').id)));
document.getElementById('btn-menu')?.addEventListener('click', () =>
  document.querySelector('.sidebar').classList.toggle('open'));

// ═════════════════  DASHBOARD  ════════════════════════════════
async function loadDashboard() {
  try {
    const s = await apiFetch('/api/stats');
    setText('stat-products', s.totals.products);
    setText('stat-orders',   s.totals.orders);
    setText('stat-users',    s.totals.users);
    setText('stat-revenue', 'Rs.' + fmt(s.totals.confirmed_revenue));
    renderMiniBar('status-bars',  s.orders_by_status,   {Confirmed:'var(--green)',Pending:'var(--orange)',Shipped:'var(--blue)',Delivered:'var(--purple)',Cancelled:'var(--red)'});
    renderMiniBar('payment-bars', s.revenue_by_payment, {CreditCard:'var(--blue)',JazzCash:'var(--orange)',EasyPaisa:'var(--green)',CashOnDelivery:'var(--purple)'});
    renderDonut('cat-donut', s.products_by_category);
  } catch(e) { toast(e.message,'error'); }
}

async function loadRecentOrders() {
  const feed = document.getElementById('activity-feed');
  if (!feed) return;
  try {
    const d = await apiFetch('/api/orders');
    const orders = d.orders.slice(-6).reverse();
    if (!orders.length) { feed.innerHTML='<div class="empty-state"><div class="empty-icon">📭</div><p>No orders yet</p></div>'; return; }
    const col = {Confirmed:'var(--green)',Pending:'var(--orange)',Shipped:'var(--blue)',Delivered:'var(--purple)',Cancelled:'var(--red)'};
    feed.innerHTML = orders.map(o=>`
      <div class="activity-item">
        <div class="activity-dot" style="background:${col[o.status]||'var(--muted)'}"></div>
        <div class="activity-body">
          <div class="activity-title">Order #${o.order_id} — ${escHtml(o.user_name)}</div>
          <div class="activity-time">${o.status} · Rs.${fmt(o.total)} · ${o.payment} · ${o.created_at}</div>
        </div>
      </div>`).join('');
  } catch(e) { feed.innerHTML='<div class="empty-state"><p>Could not load orders</p></div>'; }
}

// ═════════════════  PRODUCTS  ══════════════════════════════════
async function loadProducts() {
  document.getElementById('products-tbody').innerHTML =
    '<tr><td colspan="6" style="text-align:center;padding:28px"><div class="spinner"></div></td></tr>';
  try {
    const cat   = document.getElementById('filter-cat')?.value||'';
    const stock = document.getElementById('filter-stock')?.value||'';
    let url='/api/products', p=[];
    if(cat)           p.push('category='+cat);
    if(stock==='yes') p.push('in_stock=true');
    if(p.length) url+='?'+p.join('&');
    const d = await apiFetch(url);
    allProducts = d.products;
    setText('product-count', d.count+' product'+(d.count!==1?'s':''));
    renderProductsTable(allProducts);
  } catch(e) { toast(e.message,'error'); }
}

function renderProductsTable(rows) {
  const tb = document.getElementById('products-tbody');
  if(!rows.length){ tb.innerHTML='<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📦</div><p>No products found</p></div></td></tr>'; return; }
  tb.innerHTML = rows.map(p=>`
    <tr>
      <td class="td-bold">#${p.product_id}</td>
      <td>${escHtml(p.name)}</td>
      <td><span class="badge ${catBadge(p.category)}">${p.category}</span></td>
      <td class="fw-700">Rs.${fmt(p.price)}</td>
      <td><span class="pulse ${p.stock===0?'red':p.stock<10?'orange':''}"></span> ${p.stock}</td>
      <td>
        <button class="btn btn-outline btn-sm btn-icon" onclick="openEditStock(${p.product_id},${p.stock})">✏️</button>
        <button class="btn btn-danger  btn-sm btn-icon" onclick="deleteProduct(${p.product_id},'${escHtml(p.name)}')">🗑️</button>
      </td>
    </tr>`).join('');
}

document.getElementById('btn-add-product')?.addEventListener('click', ()=>openModal('modal-add-product'));
document.getElementById('form-add-product')?.addEventListener('submit', async e=>{
  e.preventDefault();
  const fd=new FormData(e.target);
  const body={type:fd.get('type'),product_id:+fd.get('product_id'),name:fd.get('name'),price:+fd.get('price'),stock:+fd.get('stock')};
  const t=body.type;
  if(t==='electronics') body.warranty_years=+fd.get('extra')||1;
  else if(t==='clothing') body.size=fd.get('extra')||'M';
  else if(t==='grocery')  body.expiry_date=fd.get('extra')||'N/A';
  try{ await apiFetch('/api/products',{method:'POST',body:JSON.stringify(body)}); toast('Product created!'); closeModal('modal-add-product'); e.target.reset(); loadProducts(); }
  catch(err){ toast(err.message,'error'); }
});

let editStockId=null;
function openEditStock(id,cur){ editStockId=id; document.getElementById('edit-stock-val').value=cur; openModal('modal-edit-stock'); }
document.getElementById('form-edit-stock')?.addEventListener('submit', async e=>{
  e.preventDefault();
  const stock=+document.getElementById('edit-stock-val').value;
  try{ await apiFetch(`/api/products/${editStockId}/stock`,{method:'PATCH',body:JSON.stringify({stock})}); toast('Stock updated!'); closeModal('modal-edit-stock'); loadProducts(); }
  catch(err){ toast(err.message,'error'); }
});

async function deleteProduct(id,name){
  if(!confirm(`Delete "${name}"?`)) return;
  try{ await apiFetch(`/api/products/${id}`,{method:'DELETE'}); toast(`"${name}" deleted`); loadProducts(); }
  catch(err){ toast(err.message,'error'); }
}

document.getElementById('filter-cat')?.addEventListener('change', loadProducts);
document.getElementById('filter-stock')?.addEventListener('change', loadProducts);
document.getElementById('btn-refresh-products')?.addEventListener('click', loadProducts);
document.getElementById('product-search')?.addEventListener('input', e=>{
  const q=e.target.value.toLowerCase();
  renderProductsTable(allProducts.filter(p=>p.name.toLowerCase().includes(q)||p.category.toLowerCase().includes(q)));
});
document.getElementById('product-type')?.addEventListener('change', function(){
  const label=document.getElementById('extra-label'), input=document.getElementById('extra-input');
  if(!label||!input) return;
  const map={electronics:['Warranty (years)','1'],clothing:['Size','M'],grocery:['Expiry Date','2026-12']};
  const v=map[this.value]||['Extra Field',''];
  label.textContent=v[0]; input.placeholder=v[1];
});

// ═════════════════  ORDERS  ════════════════════════════════════
async function loadOrders(){
  document.getElementById('orders-tbody').innerHTML=
    '<tr><td colspan="7" style="text-align:center;padding:28px"><div class="spinner"></div></td></tr>';
  try{
    const d=await apiFetch('/api/orders');
    allOrders=d.orders;
    setText('order-count',d.count+' order'+(d.count!==1?'s':''));
    renderOrdersTable(allOrders);
  }catch(e){ toast(e.message,'error'); }
}

function renderOrdersTable(rows){
  const tb=document.getElementById('orders-tbody');
  if(!rows.length){ tb.innerHTML='<tr><td colspan="7"><div class="empty-state"><div class="empty-icon">🛒</div><p>No orders</p></div></td></tr>'; return; }
  tb.innerHTML=rows.map(o=>`
    <tr>
      <td class="td-bold">#${o.order_id}</td>
      <td>${escHtml(o.user_name)}</td>
      <td><span class="badge badge-blue">${o.payment}</span></td>
      <td class="fw-700">Rs.${fmt(o.total)}</td>
      <td><span class="badge ${statusBadge(o.status)}">${o.status}</span></td>
      <td class="text-sm text-muted">${o.created_at}</td>
      <td>
        <select class="form-control" style="font-size:.78rem;padding:4px 8px"
          onchange="updateOrderStatus(${o.order_id},this.value)">
          ${['Pending','Confirmed','Shipped','Delivered','Cancelled'].map(s=>`<option ${s===o.status?'selected':''}>${s}</option>`).join('')}
        </select>
      </td>
    </tr>`).join('');
}

async function updateOrderStatus(id,status){
  try{ await apiFetch(`/api/orders/${id}/status`,{method:'PATCH',body:JSON.stringify({status})}); toast(`Order #${id} → ${status}`); }
  catch(e){ toast(e.message,'error'); }
}

document.getElementById('filter-order-status')?.addEventListener('change',e=>{
  const v=e.target.value;
  renderOrdersTable(v?allOrders.filter(o=>o.status===v):allOrders);
});
document.getElementById('order-search')?.addEventListener('input',e=>{
  const q=e.target.value.toLowerCase();
  renderOrdersTable(allOrders.filter(o=>String(o.order_id).includes(q)||o.user_name.toLowerCase().includes(q)));
});
document.getElementById('btn-refresh-orders')?.addEventListener('click',loadOrders);

// ── FIX #4: Product Picker for Place Order ────────────────────
document.getElementById('btn-place-order')?.addEventListener('click', openPlaceOrderModal);

async function openPlaceOrderModal(){
  orderItems=[];
  renderOrderItems();
  try{
    const d=await apiFetch('/api/products?in_stock=true');
    const sel=document.getElementById('order-product-select');
    sel.innerHTML='<option value="">— Select product —</option>'+
      d.products.map(p=>`<option value="${p.product_id}" data-price="${p.price}" data-name="${escHtml(p.name)}" data-stock="${p.stock}">
        ${escHtml(p.name)} (Rs.${fmt(p.price)}) — Stock: ${p.stock}
      </option>`).join('');
  }catch(e){ toast('Could not load products: '+e.message,'error'); }
  openModal('modal-place-order');
}

function addOrderItem(){
  const sel=document.getElementById('order-product-select');
  const opt=sel.options[sel.selectedIndex];
  const qty=parseInt(document.getElementById('order-qty').value)||1;
  if(!sel.value){ toast('Pehle product select karo','warn'); return; }
  const pid=+sel.value, price=+opt.dataset.price, name=opt.dataset.name, stock=+opt.dataset.stock;
  if(qty<1){ toast('Quantity 1 se kam nahi ho sakti','warn'); return; }
  if(qty>stock){ toast(`Sirf ${stock} units available hain`,'warn'); return; }
  const existing=orderItems.find(i=>i.product_id===pid);
  if(existing){ existing.qty=Math.min(existing.qty+qty,stock); }
  else { orderItems.push({product_id:pid,name,price,qty,stock}); }
  renderOrderItems();
  sel.value=''; document.getElementById('order-qty').value=1;
}

function removeOrderItem(pid){ orderItems=orderItems.filter(i=>i.product_id!==pid); renderOrderItems(); }

function renderOrderItems(){
  const list=document.getElementById('order-items-list');
  const emptyMsg=document.getElementById('order-empty-msg');
  const totalRow=document.getElementById('order-total-row');
  if(!orderItems.length){
    list.innerHTML=''; emptyMsg.style.display='block'; totalRow.style.display='none'; return;
  }
  emptyMsg.style.display='none'; totalRow.style.display='block';
  list.innerHTML=orderItems.map(i=>`
    <div style="display:flex;align-items:center;justify-content:space-between;
      background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:8px 12px;">
      <div>
        <span style="font-weight:600">${escHtml(i.name)}</span>
        <span style="color:var(--muted);font-size:.8rem;margin-left:8px">× ${i.qty}</span>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <span style="font-weight:700;color:var(--green)">Rs.${fmt(i.price*i.qty)}</span>
        <button type="button" onclick="removeOrderItem(${i.product_id})"
          style="background:var(--red-light);color:var(--red);border:none;border-radius:6px;padding:3px 8px;cursor:pointer;font-size:.8rem">✕</button>
      </div>
    </div>`).join('');
  const total=orderItems.reduce((s,i)=>s+i.price*i.qty,0);
  setText('order-total-val', fmt(total));
}

document.getElementById('form-place-order')?.addEventListener('submit', async e=>{
  e.preventDefault();
  // If user forgot to click +Add but has a product selected, auto-add it now
  if(!orderItems.length){
    const sel=document.getElementById('order-product-select');
    if(sel && sel.value){
      addOrderItem();           // auto-add the selected product
    }
    if(!orderItems.length){     // still empty = nothing selected at all
      toast('Koi product select nahi kiya — dropdown se product chunein','warn');
      return;
    }
  }
  const fd=new FormData(e.target);

  // FIX #1: user ID auto from next-id endpoint
  let nextId=1;
  try{ const r=await apiFetch('/api/users/next-id'); nextId=r.next_id; }catch(_){}

  const body={
    user:{id:nextId, name:fd.get('user_name'), email:fd.get('user_email')||''},
    items:orderItems.map(i=>({product_id:i.product_id,qty:i.qty})),
    payment:{method:fd.get('payment_method')},
  };
  try{
    const res=await apiFetch('/api/orders',{method:'POST',body:JSON.stringify(body)});
    toast(`Order #${res.order.order_id} placed! Rs.${fmt(res.order.total)}`);
    closeModal('modal-place-order'); e.target.reset(); orderItems=[]; renderOrderItems();
    loadOrders();
  }catch(err){ toast(err.message,'error'); }
});

// ═════════════════  USERS  ═════════════════════════════════════
async function loadUsers(){
  const tb=document.getElementById('users-tbody');
  tb.innerHTML='<tr><td colspan="5" style="text-align:center;padding:28px"><div class="spinner"></div></td></tr>';
  try{
    const d=await apiFetch('/api/users');
    setText('user-count',d.count+' user'+(d.count!==1?'s':''));
    if(!d.users.length){ tb.innerHTML='<tr><td colspan="5"><div class="empty-state"><div class="empty-icon">👤</div><p>No users</p></div></td></tr>'; return; }
    tb.innerHTML=d.users.map(u=>`
      <tr>
        <td class="td-bold">#${u.id}</td>
        <td>
          <div class="flex items-center gap-2">
            <div style="width:32px;height:32px;border-radius:50%;background:var(--purple);color:#fff;
              display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.8rem">
              ${u.name.charAt(0).toUpperCase()}
            </div>${escHtml(u.name)}
          </div>
        </td>
        <td class="text-muted">${u.email}</td>
        <td><span class="badge ${u.role==='Admin'?'badge-orange':u.role==='Seller'?'badge-purple':'badge-blue'}">${u.role}</span></td>
        <td class="text-sm text-muted">${u.created_at}</td>
      </tr>`).join('');
  }catch(e){ toast(e.message,'error'); }
}

// FIX #1: Auto-generate user ID
document.getElementById('btn-add-user')?.addEventListener('click', async ()=>{
  try{
    const r=await apiFetch('/api/users/next-id');
    document.getElementById('user-id-input').value=r.next_id;
  }catch(_){ document.getElementById('user-id-input').value=Date.now()%10000; }
  openModal('modal-add-user');
});

document.getElementById('form-add-user')?.addEventListener('submit', async e=>{
  e.preventDefault();
  const fd=new FormData(e.target);
  const body={id:+fd.get('id'),name:fd.get('name'),email:fd.get('email'),role:fd.get('role')};
  try{ await apiFetch('/api/users',{method:'POST',body:JSON.stringify(body)}); toast('User created!'); closeModal('modal-add-user'); e.target.reset(); loadUsers(); }
  catch(err){ toast(err.message,'error'); }
});

// ═════════════════  DATA FILES (FIX #2)  ══════════════════════
async function loadDataFiles(){
  const tb=document.getElementById('datafiles-tbody');
  tb.innerHTML='<tr><td colspan="5" style="text-align:center;padding:28px"><div class="spinner"></div></td></tr>';
  try{
    const d=await apiFetch('/api/datafiles');
    if(!d.files.length){ tb.innerHTML='<tr><td colspan="5"><div class="empty-state"><p>No data files found. Run main.py first.</p></div></td></tr>'; return; }
    const fmtBadge={JSON:'badge-blue',XML:'badge-orange',Pickle:'badge-green',SQLite:'badge-purple',GZIP:'badge-red',Text:'badge-orange'};
    tb.innerHTML=d.files.map(f=>`
      <tr>
        <td><span style="font-size:1.2rem">${f.icon}</span> <strong>${f.name}</strong></td>
        <td><span class="badge ${fmtBadge[f.format]||'badge-blue'}">${f.format}</span></td>
        <td style="font-size:.82rem;color:var(--muted)">${f.desc}</td>
        <td class="fw-700">${f.size_kb} KB</td>
        <td class="text-sm text-muted">${f.modified}</td>
      </tr>`).join('');
  }catch(e){ toast(e.message,'error'); }
}

// ═════════════════  LOGS — FIX #3 (real-time + LIVE badge)  ═══
function startLiveLogs(){
  logPaused=false;
  updateLiveBadge(true);
  loadLogs();
  logInterval=setInterval(()=>{ if(!logPaused) loadLogs(); }, 5000);
}

async function loadLogs(){
  const area=document.getElementById('log-area');
  const n=document.getElementById('log-lines')?.value||80;
  try{
    const d=await apiFetch(`/api/logs?n=${n}`);
    const meta=document.getElementById('log-meta');
    if(meta) meta.textContent=`${d.total_lines} total lines · showing last ${d.returned} · ${new Date().toLocaleTimeString('en-PK')}`;
    if(!d.lines.length){ area.innerHTML='<div style="color:var(--muted)">Log file khaali hai. main.py chalao pehle.</div>'; return; }
    area.innerHTML=d.lines.map(l=>{
      const cls=l.includes('[ERROR]')?'log-error':l.includes('[WARNING]')?'log-warning':l.includes('[SUCCESS]')?'log-success':'log-info';
      return `<div class="${cls}">${escHtml(l)}</div>`;
    }).join('');
    area.scrollTop=area.scrollHeight;
  }catch(e){ area.innerHTML=`<div class="log-error">${e.message}</div>`; }
}

function updateLiveBadge(live){
  const badge=document.getElementById('live-badge');
  const dot=document.getElementById('live-dot');
  if(!badge||!dot) return;
  if(live){ badge.style.background='var(--green-light)'; badge.style.borderColor='var(--green)'; badge.style.color='var(--green)'; dot.style.background='var(--green)'; }
  else     { badge.style.background='var(--orange-light)'; badge.style.borderColor='var(--orange)'; badge.style.color='var(--orange)'; dot.style.background='var(--orange)'; }
}

document.getElementById('btn-refresh-logs')?.addEventListener('click', loadLogs);
document.getElementById('log-lines')?.addEventListener('change', loadLogs);
document.getElementById('btn-pause-logs')?.addEventListener('click', function(){
  logPaused=!logPaused;
  this.textContent=logPaused?'▶ Resume':'⏸ Pause';
  updateLiveBadge(!logPaused);
});

// ═════════════════  CHARTS  ════════════════════════════════════
function renderMiniBar(cid,dataObj,colorMap){
  const el=document.getElementById(cid); if(!el) return;
  const total=Object.values(dataObj).reduce((s,v)=>s+v,0)||1;
  el.innerHTML=Object.entries(dataObj).map(([k,v])=>`
    <div class="bar-row">
      <div class="bar-meta">
        <span class="bar-label">${k}</span>
        <span class="bar-val">${typeof v==='number'&&v>999?'Rs.'+fmt(v):v}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:${((v/total)*100).toFixed(1)}%;background:${colorMap[k]||'var(--muted)'}"></div>
      </div>
    </div>`).join('');
}

function renderDonut(cid,dataObj){
  const el=document.getElementById(cid); if(!el) return;
  const colours=['var(--blue)','var(--purple)','var(--green)','var(--orange)','var(--red)'];
  const total=Object.values(dataObj).reduce((s,v)=>s+v,0)||1;
  const R=40,CX=50,CY=50,sw=16,circ=2*Math.PI*R;
  let offset=0;
  const segs=Object.entries(dataObj).map(([k,v],i)=>{
    const pct=v/total, dash=(pct*circ).toFixed(2), gap=(circ-pct*circ).toFixed(2);
    const seg=`<circle cx="${CX}" cy="${CY}" r="${R}" fill="none" stroke="${colours[i%colours.length]}" stroke-width="${sw}" stroke-dasharray="${dash} ${gap}" stroke-dashoffset="${-offset}"/>`;
    offset+=pct*circ;
    return {seg,label:k,val:v,color:colours[i%colours.length]};
  });
  el.innerHTML=`<div class="ring-chart">
    <svg width="100" height="100" viewBox="0 0 100 100" class="ring-svg">
      <circle cx="${CX}" cy="${CY}" r="${R}" fill="none" stroke="var(--border)" stroke-width="${sw}"/>
      ${segs.map(s=>s.seg).join('')}
    </svg>
    <div class="legend-grid">
      ${segs.map(s=>`<div class="legend-item"><div class="legend-dot" style="background:${s.color}"></div><span class="legend-name">${s.label}</span><span class="legend-value">${s.val}</span></div>`).join('')}
    </div>
  </div>`;
}

// ═════════════════  UTILS  ════════════════════════════════════
function setText(id,val){ const el=document.getElementById(id); if(el) el.textContent=val; }
function fmt(n){ return Number(n).toLocaleString('en-PK'); }
function escHtml(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function catBadge(c){ return c==='Electronics'?'badge-blue':c==='Clothing'?'badge-purple':'badge-green'; }
function statusBadge(s){ return s==='Confirmed'?'badge-green':s==='Shipped'?'badge-blue':s==='Delivered'?'badge-purple':s==='Cancelled'?'badge-red':'badge-orange'; }

// ── Boot ──────────────────────────────────────────────────────
showPage('pg-dashboard');

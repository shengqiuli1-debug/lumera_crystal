export const CART_STORAGE_KEY = "lumera_shop_cart";
export const CART_UPDATED_EVENT = "lumera_shop_cart_updated";

export type CartItem = {
  product_id: number;
  slug: string;
  name: string;
  price: string;
  cover_image: string;
  quantity: number;
};

function parseCart(raw: string | null): CartItem[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as CartItem[];
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item) => item && typeof item.product_id === "number" && item.quantity > 0);
  } catch {
    return [];
  }
}

export function getCart(): CartItem[] {
  if (typeof window === "undefined") return [];
  return parseCart(window.localStorage.getItem(CART_STORAGE_KEY));
}

export function saveCart(items: CartItem[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
  window.dispatchEvent(new Event(CART_UPDATED_EVENT));
}

export function setCart(items: CartItem[]) {
  saveCart(items);
}

export function addToCart(item: Omit<CartItem, "quantity">, quantity = 1): CartItem[] {
  const cart = getCart();
  const found = cart.find((line) => line.product_id === item.product_id);
  if (found) {
    found.quantity += Math.max(1, quantity);
  } else {
    cart.push({ ...item, quantity: Math.max(1, quantity) });
  }
  saveCart(cart);
  return cart;
}

export function updateCartQuantity(productId: number, quantity: number): CartItem[] {
  const cart = getCart();
  const next = cart
    .map((line) => (line.product_id === productId ? { ...line, quantity: Math.max(0, quantity) } : line))
    .filter((line) => line.quantity > 0);
  saveCart(next);
  return next;
}

export function removeFromCart(productId: number): CartItem[] {
  const next = getCart().filter((line) => line.product_id !== productId);
  saveCart(next);
  return next;
}

export function clearCart() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(CART_STORAGE_KEY);
  window.dispatchEvent(new Event(CART_UPDATED_EVENT));
}

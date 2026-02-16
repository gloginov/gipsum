export interface CartItem {
  id: number
  product_id: number
  product_name: string
  product_slug: string
  quantity: number
  price: string
  total: string
  main_image: string | null
  stock: number
  in_stock: boolean
}

export interface Cart {
  items: CartItem[]
  total: string
  count: number
  is_authenticated: boolean
}

export interface CartAddPayload {
  product_id: number
  quantity: number
  override?: boolean
}

export interface CartUpdatePayload {
  product_id: number
  quantity: number
}

export interface CartRemovePayload {
  product_id: number
}
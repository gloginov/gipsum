export type Filters = {
  category?: string
  min_price?: number | null
  max_price?: number | null
  in_stock: boolean
  is_new: boolean
  is_featured: boolean
  is_bestseller: boolean
  search?: string
}

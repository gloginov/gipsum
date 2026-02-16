export type Product = {
  id: number
  name: string
  slug: string
  short_description: string
  description?: string
  price: number
  old_price?: number
  stock: number
  is_available: boolean
  is_bestseller: boolean
  is_new: boolean
  is_featured: boolean
  main_image: {
    url: string
    alt: string
  } | null
  categories?: {
    id: number
    name: string
    slug: string
  }[]
}
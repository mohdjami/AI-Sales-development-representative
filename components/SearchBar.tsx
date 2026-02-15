import { Input } from "@/components/ui/input"

export default function SearchBar() {
  return (
    <div className="w-full max-w-md">
      <Input type="text" placeholder="Search prospects..." className="w-full" />
    </div>
  )
}


import { useQuery } from "@tanstack/react-query";
import { fetchCurrentUser } from "../api/auth";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["currentUser"],
    queryFn: fetchCurrentUser,
    // do not retry too many times if auth fails
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

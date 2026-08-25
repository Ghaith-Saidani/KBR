import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import type { ReactNode } from "react";

import  AuthSession  from "../components/common/AuthSession";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },

    mutations: {
      retry: 0,
    },
  },
});


interface AppProvidersProps {
  children: ReactNode;
}


export function AppProviders({
  children,
}: AppProvidersProps) {
  return (
    <QueryClientProvider
      client={queryClient}
    >
      <AuthSession />

      {children}
    </QueryClientProvider>
  );
}
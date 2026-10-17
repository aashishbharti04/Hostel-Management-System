import React from "react";
import { createRoot } from "react-dom/client";
import { createClient } from "@supabase/supabase-js";
import App from "./App";
import "./style.css";
const url=import.meta.env.VITE_SUPABASE_URL as string|undefined;
const key=import.meta.env.VITE_SUPABASE_ANON_KEY as string|undefined;
const client=url&&key?createClient(url,key,{auth:{persistSession:true,autoRefreshToken:true}}):null;
createRoot(document.getElementById("root")!).render(<React.StrictMode><App supabase={client}/></React.StrictMode>);

import { defineConfig } from "vite";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const NOTEMAP_ROOT = path.resolve(__dirname, "../../");

 export default defineConfig({
   server: {
     fs: { allow: [NOTEMAP_ROOT] }
   },
   define: {
     __NOTEMAP_ROOT__: JSON.stringify(NOTEMAP_ROOT)
   }
 });
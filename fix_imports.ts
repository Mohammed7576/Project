import fs from "fs";
import path from "path";

function replaceInDir(dir: string, replacements: {from: RegExp, to: string}[]) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        if (fs.statSync(fullPath).isDirectory()) {
            replaceInDir(fullPath, replacements);
        } else if (fullPath.endsWith(".tsx") || fullPath.endsWith(".ts")) {
            let content = fs.readFileSync(fullPath, "utf-8");
            let changed = false;
            for (const r of replacements) {
                if (r.from.test(content)) {
                    content = content.replace(r.from, r.to);
                    changed = true;
                }
            }
            if (changed) {
                fs.writeFileSync(fullPath, content, "utf-8");
                console.log("Updated", fullPath);
            }
        }
    }
}

replaceInDir("src/pages", [
    { from: /@\/components\/ui/g, to: "../components/ui" },
    { from: /@\/lib/g, to: "../lib" }
]);

replaceInDir("src/components/ui", [
    { from: /@\/components\/ui\//g, to: "./" },
    { from: /@\/lib/g, to: "../../lib" }
]);

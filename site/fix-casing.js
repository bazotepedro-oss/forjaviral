const fs = require('fs');
const path = require('path');

function walk(dir) {
  for (const f of fs.readdirSync(dir)) {
    const p = path.join(dir, f);
    if (fs.statSync(p).isDirectory()) {
      walk(p);
    } else if (f.endsWith('.tsx') || f.endsWith('.ts')) {
      let c = fs.readFileSync(p, 'utf8');
      const n = c
        .replace(/from '@\/components\/Navbar'/g, "from '@/components/navbar'")
        .replace(/from '@\/components\/Footer'/g, "from '@/components/footer'");
      if (n !== c) {
        fs.writeFileSync(p, n, 'utf8');
        console.log('fixed:', p);
      }
    }
  }
}

walk(path.join(__dirname, 'app'));
console.log('done');

// Run the actual inline application script with an offline DOM boundary.
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');

function harness() {
    const html = readFileSync('templates/index.html', 'utf8');
    const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
    const elements = {};
    const downloads = [];
    const context = vm.createContext({
        document: {
            addEventListener() {},
            getElementById: id => elements[id] || null,
            createElement: tag => ({
                tag, style: {}, children: [],
                appendChild(child) { this.children.push(child); },
                click() { downloads.push(this); },
            }),
        },
        alert: message => downloads.push(message),
        Blob,
        URL: { createObjectURL: blob => { downloads.push(blob); return 'blob:fixture'; },
            revokeObjectURL() {} },
        fetch() { throw new Error('Live API access is forbidden'); },
        console,
    });
    vm.runInContext(script, context);
    return { run: code => vm.runInContext(code, context), elements, downloads };
}

test('manual usage accepts empty, single counts, and usage/entitlement pairs', () => {
    const { run } = harness();
    for (const [input, used, entitled] of [
        ['', 0, 0], ['  ', 0, 0], ['12', 12, 12], [' 8 / 20 ', 8, 20],
        ['0/5', 0, 5], ['bad', 0, 0],
    ]) {
        const parsed = run(`parseUsageEntitled(${JSON.stringify(input)})`);
        assert.equal(parsed.used, used);
        assert.equal(parsed.entitled, entitled);
    }
});

test('SUB-AI adds all five components, uses entitlement, and marks deficits', () => {
    const { run, elements } = harness();
    const rows = [];
    elements.tableBody = { appendChild: row => rows.push(row) };
    run(`purchasedLicenses = {'SUB-AI': 10, 'SUB-MAN': 2, 'SUB-EX24': 3};
        lastSortedLicenseTypes = ['SUB-MAN','SUB-VNA','SUB-AST','SUB-ENG','SUB-PMA','SUB-EX24','SUB-WAN'];
        lastLicenseTotals = {'SUB-MAN': {used: 1, entitled: 7},
            'SUB-VNA': {used: 0, entitled: 12}};
        calculateRemaining();`);
    const cells = rows[0].children;
    assert.match(cells[0].innerHTML, />5<\/strong>/);
    assert.match(cells[1].innerHTML, />-2<\/strong>/);
    assert.equal(cells[1].className, 'text-danger');
    for (const cell of cells.slice(2, 5)) assert.match(cell.innerHTML, />10<\/strong>/);
    assert.match(cells[5].innerHTML, />3<\/strong>/);
    assert.equal(cells[6].textContent, '-');
});

test('remaining calculation replaces stale rows and handles no purchases', () => {
    const { run, elements, downloads } = harness();
    let removed = false;
    elements.remainingRow = { remove: () => { removed = true; } };
    run('calculateRemaining()');
    assert.equal(removed, true);
    assert.match(downloads[0], /at least one purchased license/);
});

test('CSV preserves manual inputs, license ratios, commas, and quoted names', async () => {
    const { run, elements, downloads } = harness();
    elements.tableHeader = { querySelectorAll: () => [{ textContent: 'Org' }, { textContent: 'SUB-MAN' }] };
    const cell = (textContent, input = null) => ({ textContent, querySelector: () => input });
    elements.tableBody = { querySelectorAll: () => [
        { querySelectorAll: () => [cell('Org "North", Inc'), cell('8 / 10')] },
        { querySelectorAll: () => [cell('', { value: 'Manual' }), cell('', { value: '2/5' })] },
    ] };
    run('exportCSV()');
    assert.equal(await downloads[0].text(),
        '"Org","SUB-MAN"\n"Org ""North"", Inc"," 8 / 10"\n"Manual"," 2/5"\n');
    assert.match(downloads[1].download, /^mist_license_comparison_.*\.csv$/);
});

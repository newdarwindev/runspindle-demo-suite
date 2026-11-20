"""Presentation-only enhancements. No upstream dependency or mutation authority."""
import html

WORKSPACES = {
 'mock-excel': ('Your work, reconciled.', 'Inspect saved tables and preserve every unrelated cell.', 'Results ledger'),
 'mock-mail': ('A calmer inbox.', 'Read the invitation. Prepare a draft. Keep the next move yours.', 'Correspondence'),
 'mock-counterorders': ('Tomorrow starts here.', 'Turn confirmed orders into a clear morning bake list.', 'Morning prep'),
 'mock-job-board': ('Find the right next step.', 'Discover and save a suitable fictional contract before applying.', 'Opportunities'),
 'mock-applicant-portal': ('An application with intention.', 'Prepare your answer, review it, then move to the next stage.', 'Application journey'),
 'mock-interview-room': ('Make room for a conversation.', 'Keep the interview context visible and the human in control.', 'Interview room'),
 'mock-coderpad': ('Understand. Solve. Review.', 'Read the assistance policy before attempting an assessment.', 'Assessment bench'),
 'mock-issue-tracker': ('From an issue to evidence.', 'Connect the reported problem with a reviewed fix and test results.', 'Issue triage'),
 'mock-code-workspace': ('Build a fix you can prove.', 'Inspect the defect, edit the fixture, test and prepare a review.', 'Engineering desk'),
 'mock-bank': ('Clarity in every entry.', 'Match the exact invoice reference, account and amount.', 'Deposit reconciliation'),
 'mock-vendor-portal': ('Keep every project moving.', 'Inspect invoice status within the correct contractor and project.', 'Project accounts'),
 'mock-timesheet-portal': ('Hours with a clear status.', 'Separate approved work from hours still awaiting a decision.', 'Weekly billing'),
 'mock-marketplace': ('Follow the parcel, not the label.', 'Use carrier evidence to distinguish a pending return from transit.', 'Returns studio'),
 'mock-supplier-portal': ('Fresh orders. Honest totals.', 'Pack confirmed quantities and surface unavailable sources as gaps.', 'Packing desk'),
}

CSS = r"""
/* Shared usability, while child-owned brand palettes and typography remain distinct. */
[hidden]{display:none!important}html{scroll-behavior:smooth;scroll-padding-top:180px}
.skip-link{position:fixed;left:16px;top:12px;z-index:100;background:var(--surface);width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}.skip-link:focus{width:auto;height:auto;clip-path:none;padding:12px}
header{box-shadow:0 4px 24px #00000008}main{max-width:1200px}
.workspace-hero{padding:34px 0 22px;border-bottom:1px solid var(--accent);margin-bottom:24px;display:grid;grid-template-columns:1fr auto;gap:24px;align-items:end}
.workspace-kicker{font-size:11px;font-weight:bold;text-transform:uppercase;letter-spacing:.17em;color:var(--accent)}
.workspace-hero h2{font:clamp(26px,4vw,46px)/1.12 var(--display-font);margin:12px 0;max-width:740px}.workspace-hero p{max-width:600px;margin:0;opacity:.85}
.workspace-seal{font:italic 68px/1 var(--display-font);color:var(--accent);opacity:.35}
.workspace-nav{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}.workspace-nav a{color:var(--ink);text-decoration:none;border:1px solid var(--accent);border-radius:var(--radius);padding:8px 14px;font-size:13px}.workspace-nav a:hover{background:var(--canvas)}
section{box-shadow:0 8px 22px #00000004}section h2{letter-spacing:-.025em}button{transition:filter .15s,transform .15s}button:active{transform:translateY(1px)}button:disabled{cursor:not-allowed;opacity:.55}
#sheet-view{overflow-x:auto;max-width:100%}#sheet-view table{min-width:420px}#sheet-view th{font-size:11px;letter-spacing:.07em;text-transform:uppercase;background:var(--canvas)}#sheet-view td{font-size:14px;max-width:420px;overflow-wrap:anywhere}#sheet-view tr:hover td{background:var(--canvas)}
.record-toolbar{display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap;padding:14px 0}.record-toolbar input{min-width:180px;margin:0}.record-toolbar label{font-size:13px}.record-count{font:12px var(--body-font);opacity:.8}.record-empty{padding:24px;border:1px dashed var(--accent);border-radius:var(--radius)}
#status{font-size:14px;overflow-wrap:anywhere}details{border-top:1px solid var(--canvas);padding:10px 0}summary{font-size:13px;color:var(--accent)!important}
@media(max-width:640px){html{scroll-padding-top:20px}header{position:relative!important}.workspace-hero{padding-top:16px;gap:8px}.workspace-seal{font-size:42px}.workspace-nav a{flex:1;text-align:center;padding:8px}.record-toolbar{align-items:stretch}.record-toolbar label,.record-toolbar input{width:100%}.record-toolbar input{margin-top:6px}section{margin:14px 0}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}button{transition:none}}
"""

JS = r"""
// View filters never change source records or persisted results.
const recordView=$('sheet-view'), recordFilter=$('record-filter');
function filterRecords(){
 const query=recordFilter.value.trim().toLocaleLowerCase();let total=0,shown=0;
 for(const row of recordView.querySelectorAll('tr')){if(row.querySelector('th'))continue;total++;row.hidden=!!query&&!row.textContent.toLocaleLowerCase().includes(query);if(!row.hidden)shown++;}
 $('record-count').textContent=total?`${shown} of ${total} rows visible`:'No tabular records loaded';
 $('record-empty').hidden=!(total&&shown===0);
}
recordFilter.addEventListener('input',filterRecords);
new MutationObserver(filterRecords).observe(recordView,{childList:true,subtree:true});filterRecords();
if(APP!=='mock-excel')$('source-links').closest('label').hidden=true;
$('status').setAttribute('role','status');$('status').setAttribute('aria-live','polite');
// Hide wrappers of irrelevant inputs, not just the input with an orphan label.
for(const id of ['cell-key','cell-value'])if($(id).hidden)$(id).closest('label').hidden=true;
const rich=$('rich-controls');if(![...rich.querySelectorAll('button')].some(x=>!x.hidden))rich.hidden=true;
"""

def enhance(content, app):
 headline, description, category = WORKSPACES[app]
 index = list(WORKSPACES).index(app) + 1
 hero = ('<div class="workspace-hero"><div><span class="workspace-kicker">'+html.escape(category)+'</span><h2>'+html.escape(headline)+'</h2><p>'+html.escape(description)+'</p></div><span class="workspace-seal" aria-hidden="true">'+f'{index:02d}'+'</span></div><nav class="workspace-nav" aria-label="Workspace sections"><a href="#session-panel">01 · Access</a><a href="#records-panel">02 · Records</a><a href="#editor">03 · Work area</a></nav>')
 content=content.replace('<main><section>', '<a class="skip-link" href="#workspace">Skip to workspace</a><main id="workspace">'+hero+'<section id="session-panel">',1)
 content=content.replace('<section><h2>Selected account records</h2>', '<section id="records-panel"><h2>Selected account records</h2>',1)
 toolbar='<div class="record-toolbar"><label>Filter loaded records <input id="record-filter" type="search" placeholder="Find a reference, status or name" aria-controls="sheet-view"></label><span id="record-count" class="record-count" role="status" aria-live="polite"></span></div><p id="record-empty" class="record-empty" hidden>No loaded rows match this filter. Clear it to see all records.</p>'
 content=content.replace('<div id="sheet-view">',toolbar+'<div id="sheet-view">',1)
 return content.replace('</style>',CSS+'</style>',1).replace('</script>',JS+'</script>',1)

import subprocess,unittest
from pathlib import Path
class OperatorAdapterTests(unittest.TestCase):
 def test_manual_waits_without_click_and_scripted_is_scoped(self):
  script=r'''
const assert=require('assert');const {createOperator}=require('./tools/fixture-operator.cjs');
(async()=>{
 for(const mode of ['manual','scripted']){
  let clicks=0,fills=0;const events=[];
  const page={url:()=> 'http://localhost:4300',locator:()=>({click:async()=>{clicks++},fill:async()=>{fills++}}),waitForResponse:async(predicate)=>{assert(predicate({url:()=> 'http://localhost:4300/ui',request:()=>({method:()=> 'POST',postDataJSON:()=>({action:'signin'})})}));return {json:async()=>({status:'verified'})}}};
  const op=createOperator(mode,(kind,data)=>events.push({kind,...data}));assert.equal((await op.perform(page,'challenge')).status,'verified');await op.account(page,'demo');assert.equal(clicks,mode==='manual'?0:1);assert.equal(fills,mode==='manual'?0:1);assert(events.some(e=>e.kind===mode+'-operator-duration'));await assert.rejects(op.perform(page,'save'),/outside operator scope/);
 }
 assert.throws(()=>createOperator('unsafe',()=>{}),/Operator mode/);
})().catch(e=>{console.error(e);process.exit(1)});
'''
  result=subprocess.run(['node','-e',script],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)

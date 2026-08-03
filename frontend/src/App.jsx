import { useState } from 'react';
import EasyCard from './components/EasyCard';
import StepShell from './components/StepShell';
import OptionCard from './components/OptionCard';
import ResultCard from './components/ResultCard';
import FacilityMatches from './components/FacilityMatches';
import FacilityUpdatePage from './components/FacilityUpdatePage';
import { CMS_LEVEL_QUOTA, HOUSEHOLD_COPAY_RATE, calculateSubsidy } from './data/subsidyRules';
import { DISTRICTS } from './data/districts';

const TOTAL_STEPS = 4;

const IDENTITY_OPTIONS = [
  { value: 'elderly_65', label: '65 歲以上長者', sublabel: '失能且需要照顧' },
  { value: 'aboriginal_55', label: '55 歲以上原住民', sublabel: '失能且需要照顧' },
  { value: 'disabled', label: '領有身心障礙證明者', sublabel: '任何年齡' },
  { value: 'not_sure', label: '不確定 / 尚未確認資格', sublabel: '仍可先試算，正式資格以照管中心評估為準' },
];

export default function App() {
  // Simple path-based routing -- just two "pages" total, so a full router
  // library would be overkill. /update/<token> shows the facility
  // self-update page; everything else shows the subsidy wizard.
  const pathMatch = window.location.pathname.match(/^\/update\/(.+)$/);
  if (pathMatch) {
    return <FacilityUpdatePage token={pathMatch[1]} />;
  }

  return <SubsidyWizard />;
}

function SubsidyWizard() {
  const [step, setStep] = useState(1);
  const [identity, setIdentity] = useState(null);
  const [cmsLevel, setCmsLevel] = useState(null);
  const [householdType, setHouseholdType] = useState(null);
  const [district, setDistrict] = useState('');
  const [done, setDone] = useState(false);

  const result = cmsLevel && householdType ? calculateSubsidy(cmsLevel, householdType) : null;

  const restart = () => {
    setStep(1);
    setIdentity(null);
    setCmsLevel(null);
    setHouseholdType(null);
    setDistrict('');
    setDone(false);
  };

  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-10 gap-10">
      <header className="text-center max-w-lg">
        <h1 className="font-display text-3xl font-extrabold" style={{ color: 'var(--color-teal)' }}>
          桃園長照導航
        </h1>
        <p className="text-ink/60 mt-1">4 步驟試算長照給付額度，並找到附近的日照中心</p>
      </header>

      <EasyCard
        step={done ? TOTAL_STEPS : step - 1}
        totalSteps={TOTAL_STEPS}
        cmsLevel={cmsLevel}
        householdLabel={householdType ? HOUSEHOLD_COPAY_RATE[householdType].label : null}
        quota={result?.quota}
      />

      <main className="w-full">
        {!done && step === 1 && (
          <StepShell
            eyebrow="第 1 步 / 共 4 步"
            title="請問是為誰試算？"
            description="長照給付適用於符合資格的失能者，先確認基本身分。"
            onNext={() => setStep(2)}
            nextDisabled={!identity}
          >
            {IDENTITY_OPTIONS.map((opt) => (
              <OptionCard
                key={opt.value}
                label={opt.label}
                sublabel={opt.sublabel}
                selected={identity === opt.value}
                onClick={() => setIdentity(opt.value)}
              />
            ))}
          </StepShell>
        )}

        {!done && step === 2 && (
          <StepShell
            eyebrow="第 2 步 / 共 4 步"
            title="失能需要等級（CMS）大約是幾級？"
            description="此等級由照顧管理專員到府評估後核定。如果已收到核定通知，請選擇該等級；若尚未評估，可先選擇預估等級試算。"
            onBack={() => setStep(1)}
            onNext={() => setStep(3)}
            nextDisabled={!cmsLevel}
          >
            {Object.keys(CMS_LEVEL_QUOTA).map((level) => (
              <OptionCard
                key={level}
                label={`CMS 第 ${level} 級`}
                sublabel={`每月額度上限 NT$ ${CMS_LEVEL_QUOTA[level].toLocaleString('zh-Hant-TW')}`}
                selected={cmsLevel === Number(level)}
                onClick={() => setCmsLevel(Number(level))}
              />
            ))}
          </StepShell>
        )}

        {!done && step === 3 && (
          <StepShell
            eyebrow="第 3 步 / 共 4 步"
            title="家庭經濟狀況（身分別）"
            description="自付比例依身分別而不同，這會影響最終需要自付的金額。"
            onBack={() => setStep(2)}
            onNext={() => setStep(4)}
            nextDisabled={!householdType}
          >
            {Object.entries(HOUSEHOLD_COPAY_RATE).map(([key, val]) => (
              <OptionCard
                key={key}
                label={val.label}
                sublabel={`自付比例 ${(val.rate * 100).toFixed(0)}%`}
                selected={householdType === key}
                onClick={() => setHouseholdType(key)}
              />
            ))}
          </StepShell>
        )}

        {!done && step === 4 && (
          <StepShell
            eyebrow="第 4 步 / 共 4 步"
            title="您在桃園市的哪個行政區？"
            description="我們會找出該行政區內的日間照顧中心給您參考。"
            onBack={() => setStep(3)}
            onNext={() => setDone(true)}
            nextDisabled={!district}
            nextLabel="查看結果"
          >
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border-2 text-base bg-white"
              style={{ borderColor: 'var(--color-sage)' }}
            >
              <option value="" disabled>請選擇行政區</option>
              {DISTRICTS.map((d) => (
                <option key={d} value={d}>{d}區</option>
              ))}
            </select>
          </StepShell>
        )}

        {done && result && (
          <div className="w-full max-w-lg mx-auto space-y-10">
            <ResultCard result={result} onRestart={restart} />
            <div>
              <h2 className="font-display text-xl font-extrabold mb-4" style={{ color: 'var(--color-teal)' }}>
                {district}區的日間照顧中心
              </h2>
              <FacilityMatches district={district} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

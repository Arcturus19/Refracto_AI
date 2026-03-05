import React from 'react'
import { Sparkles } from 'lucide-react'

export default function AIReasoning() {
    return (
        <div className="bg-sky-50 p-5 rounded-xl border border-sky-100">
            <h3 className="font-bold text-sky-800 flex items-center gap-2 mb-3">
                <Sparkles size={18} className="fill-sky-800" />
                AI Reasoning
            </h3>
            <ul className="space-y-2">
                <li className="flex items-start gap-2 text-sm text-sky-900 leading-relaxed">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-sky-500 flex-shrink-0" />
                    <span>Higher <strong>Cup-to-Disc ratio</strong> (0.65) detected in the optic disc region, suggesting early signs of Glaucomatous changes.</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-sky-900 leading-relaxed">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-sky-500 flex-shrink-0" />
                    <span>Microaneurysms detected near the macula, correlating with <strong>Mild Non-Proliferative Diabetic Retinopathy</strong>.</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-sky-900 leading-relaxed">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-sky-500 flex-shrink-0" />
                    <span>RNFL thickness map shows localized thinning in the superior quadrant.</span>
                </li>
            </ul>
        </div>
    )
}

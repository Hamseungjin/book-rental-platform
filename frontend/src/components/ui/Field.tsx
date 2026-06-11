import { forwardRef, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'
export function Label({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) { return <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium text-slate-700">{children}</label> }
const style = 'w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 disabled:bg-slate-100'
export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>((p, ref) => <input ref={ref} className={`${style} ${p.className ?? ''}`} {...p} />)
export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>((p, ref) => <select ref={ref} className={`${style} ${p.className ?? ''}`} {...p} />)
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>((p, ref) => <textarea ref={ref} className={`${style} min-h-28 ${p.className ?? ''}`} {...p} />)

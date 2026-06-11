import { ArrowRight, BookOpen, Handshake, ShieldCheck, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card } from '../components/ui/Card'
const features: { icon: LucideIcon; title: string; text: string }[] = [
  { icon: BookOpen, title: '승인된 도서', text: '운영자 검토를 통과한 도서만 공개됩니다.' },
  { icon: Handshake, title: '간단한 대여 흐름', text: '요청부터 승인, 반납까지 상태를 한눈에 확인합니다.' },
  { icon: ShieldCheck, title: '역할별 업무 공간', text: '대여자, 등록자, 운영자에게 필요한 화면을 제공합니다.' },
]
export function HomePage() { return <div><section className="overflow-hidden rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900 to-brand-700 px-6 py-14 text-white md:px-12"><p className="text-sm font-semibold text-brand-50">함께 읽고, 함께 나누는 도서 플랫폼</p><h1 className="mt-3 max-w-3xl text-4xl font-bold leading-tight md:text-5xl">필요한 책을 발견하고<br/>안전하게 대여하세요.</h1><p className="mt-5 max-w-2xl text-slate-300">승인된 도서를 둘러보고 대여를 요청하거나, 소장한 책을 등록해 다른 독자와 공유할 수 있습니다.</p><Link to="/books" className="mt-8 inline-flex items-center gap-2 rounded-lg bg-white px-5 py-3 font-semibold text-slate-900">도서 둘러보기 <ArrowRight className="h-4 w-4"/></Link></section><div className="mt-8 grid gap-4 md:grid-cols-3">{features.map(({icon: Icon,title,text}) => <Card key={title}><Icon className="h-8 w-8 text-brand-600"/><h2 className="mt-4 font-bold">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-600">{text}</p></Card>)}</div></div> }

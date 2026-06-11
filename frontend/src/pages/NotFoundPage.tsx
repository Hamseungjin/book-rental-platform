import { Link } from 'react-router-dom'
import { EmptyState } from '../components/ui/Feedback'
export function NotFoundPage(){return <div><EmptyState title="페이지를 찾을 수 없습니다." description="요청한 주소를 다시 확인해 주세요."/><Link className="mt-4 block text-center font-semibold text-brand-700" to="/">홈으로 이동</Link></div>}

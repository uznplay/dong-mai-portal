import React from 'react';
import { createRoot } from 'react-dom/client';
import {
    Building2,
    FileText,
    Calendar,
    MessageSquare,
    Phone,
    Mail,
    MapPin,
    Clock,
    Users,
    Award,
    ChevronRight,
    CheckCircle,
    TrendingUp
} from 'lucide-react';

// Main App Component
function App() {
    const [activeSection, setActiveSection] = React.useState('home');

    return (
        <div className="min-h-screen">
            {/* Header */}
            <Header activeSection={activeSection} setActiveSection={setActiveSection} />

            {/* Hero Section */}
            <Hero />

            {/* Stats Section */}
            <Stats />

            {/* Services Section */}
            <Services />

            {/* Features Section */}
            <Features />

            {/* Contact Section */}
            <Contact />

            {/* Footer */}
            <Footer />
        </div>
    );
}

// Header Component
function Header({ activeSection, setActiveSection }) {
    return (
        <header className="bg-white shadow-md sticky top-0 z-50">
            <div className="container mx-auto px-4 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="w-12 h-12 bg-red-primary rounded-lg flex items-center justify-center">
                            <Building2 className="text-white" size={28} />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">Phường Đông Mai</h1>
                            <p className="text-sm text-gray-600">Hành chính phục vụ</p>
                        </div>
                    </div>

                    <nav className="hidden md:flex space-x-8">
                        <a href="#home" className="text-gray-700 hover:text-red-primary transition-colors font-medium">Trang chủ</a>
                        <a href="#services" className="text-gray-700 hover:text-red-primary transition-colors font-medium">Dịch vụ</a>
                        <a href="#procedures" className="text-gray-700 hover:text-red-primary transition-colors font-medium">Thủ tục</a>
                        <a href="#contact" className="text-gray-700 hover:text-red-primary transition-colors font-medium">Liên hệ</a>
                    </nav>

                    <button className="btn-primary">
                        Đặt lịch hẹn
                    </button>
                </div>
            </div>
        </header>
    );
}

// Hero Component
function Hero() {
    return (
        <section className="hero-section relative" id="home">
            <div className="container mx-auto px-4 relative z-10">
                <div className="text-center text-white max-w-4xl mx-auto animate-fade-in-up">
                    <h2 className="text-5xl md:text-6xl font-bold mb-6 font-soft">
                        Chào mừng đến với<br />Phường Đông Mai Số
                    </h2>
                    <p className="text-xl md:text-2xl mb-8 text-white/90">
                        Hệ thống chuyển đổi số hành chính công.<br />
                        Lấy sự hài lòng của người dân làm mục tiêu phục vụ.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <button className="bg-white text-red-primary px-8 py-4 rounded-full font-semibold text-lg hover-lift hover:shadow-2xl">
                            Tra cứu thủ tục
                        </button>
                        <button className="bg-transparent border-2 border-white text-white px-8 py-4 rounded-full font-semibold text-lg hover:bg-white hover:text-red-primary transition-all">
                            Liên hệ tư vấn
                        </button>
                    </div>
                </div>
            </div>

            {/* Decorative elements */}
            <div className="absolute bottom-0 left-0 right-0">
                <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M0 120L60 105C120 90 240 60 360 45C480 30 600 30 720 37.5C840 45 960 60 1080 67.5C1200 75 1320 75 1380 75L1440 75V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="rgb(249, 250, 251)" />
                </svg>
            </div>
        </section>
    );
}

// Stats Component
function Stats() {
    const stats = [
        { icon: Users, value: "10,000+", label: "Người dân phục vụ" },
        { icon: FileText, value: "156", label: "Loại thủ tục" },
        { icon: Award, value: "98%", label: "Hài lòng" },
        { icon: TrendingUp, value: "24/7", label: "Hỗ trợ trực tuyến" }
    ];

    return (
        <section className="py-16 bg-gray-50">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {stats.map((stat, index) => (
                        <div key={index} className="card text-center hover-lift animate-fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-primary/10 rounded-full mb-4">
                                <stat.icon className="text-red-primary" size={32} />
                            </div>
                            <h3 className="text-4xl font-bold text-gray-900 mb-2">{stat.value}</h3>
                            <p className="text-gray-600 font-medium">{stat.label}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}

// Services Component
function Services() {
    const services = [
        {
            icon: FileText,
            title: "Tra cứu thủ tục",
            description: "Tra cứu nhanh chóng các thủ tục hành chính, biểu mẫu và hồ sơ cần thiết",
            color: "bg-blue-500"
        },
        {
            icon: Calendar,
            title: "Đặt lịch hẹn",
            description: "Đặt lịch hẹn trực tuyến, tránh chờ đợi lâu, tiết kiệm thời gian",
            color: "bg-green-500"
        },
        {
            icon: MessageSquare,
            title: "Trợ lý ảo AI",
            description: "Tư vấn tự động 24/7 về thủ tục, giấy tờ và quy trình hành chính",
            color: "bg-purple-500"
        },
        {
            icon: Phone,
            title: "Tổng đài hỗ trợ",
            description: "Đội ngũ chuyên viên sẵn sàng hỗ trợ qua điện thoại và email",
            color: "bg-orange-500"
        }
    ];

    return (
        <section className="py-20 bg-white" id="services">
            <div className="container mx-auto px-4">
                <div className="text-center mb-16 animate-fade-in-up">
                    <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4 font-soft">
                        Dịch vụ của chúng tôi
                    </h2>
                    <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                        Cung cấp các dịch vụ hành chính công hiện đại, tiện lợi và nhanh chóng
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {services.map((service, index) => (
                        <div key={index} className="card service-card hover-lift group animate-fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
                            <div className={`inline-flex items-center justify-center w-16 h-16 ${service.color} rounded-2xl mb-6 group-hover:scale-110 transition-transform`}>
                                <service.icon className="text-white" size={32} />
                            </div>
                            <h3 className="text-xl font-bold text-gray-900 mb-3">{service.title}</h3>
                            <p className="text-gray-600 mb-4">{service.description}</p>
                            <a href="#" className="inline-flex items-center text-red-primary font-semibold hover:gap-2 transition-all">
                                Tìm hiểu thêm
                                <ChevronRight size={20} />
                            </a>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}

// Features Component
function Features() {
    const features = [
        "Thủ tục đơn giản, nhanh chóng",
        "Hệ thống quản lý hiện đại",
        "Bảo mật thông tin tuyệt đối",
        "Đội ngũ chuyên nghiệp",
        "Hỗ trợ trực tuyến 24/7",
        "Minh bạch quy trình"
    ];

    return (
        <section className="py-20 bg-gradient-primary" id="procedures">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                    <div className="text-white animate-fade-in-up">
                        <h2 className="text-4xl md:text-5xl font-bold mb-6 font-soft">
                            Tại sao chọn<br />Đông Mai Số?
                        </h2>
                        <p className="text-xl mb-8 text-white/90">
                            Chúng tôi cam kết mang đến trải nghiệm dịch vụ hành chính công tốt nhất cho người dân phường Đông Mai
                        </p>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {features.map((feature, index) => (
                                <div key={index} className="flex items-center space-x-3 animate-fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
                                    <CheckCircle className="text-white flex-shrink-0" size={24} />
                                    <span className="text-lg">{feature}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="relative animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
                        <div className="bg-white rounded-3xl p-8 shadow-2xl">
                            <h3 className="text-2xl font-bold text-gray-900 mb-6">Quy trình thực hiện</h3>

                            <div className="space-y-6">
                                {['Tra cứu thủ tục', 'Chuẩn bị hồ sơ', 'Nộp hồ sơ trực tuyến', 'Nhận kết quả'].map((step, index) => (
                                    <div key={index} className="flex items-start space-x-4">
                                        <div className="flex-shrink-0 w-10 h-10 bg-red-primary text-white rounded-full flex items-center justify-center font-bold">
                                            {index + 1}
                                        </div>
                                        <div>
                                            <h4 className="font-semibold text-gray-900 text-lg">{step}</h4>
                                            <p className="text-gray-600">Hoàn thành nhanh chóng và dễ dàng</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}

// Contact Component
function Contact() {
    const contactInfo = [
        { icon: MapPin, title: "Địa chỉ", content: "Phường Đông Mai, Thành phố Bắc Ninh, Tỉnh Bắc Ninh" },
        { icon: Phone, title: "Điện thoại", content: "024.xxxx.xxxx" },
        { icon: Mail, title: "Email", content: "dongmai@bacninh.gov.vn" },
        { icon: Clock, title: "Giờ làm việc", content: "Thứ 2 - Thứ 6: 7:30 - 17:00" }
    ];

    return (
        <section className="py-20 bg-gray-50" id="contact">
            <div className="container mx-auto px-4">
                <div className="text-center mb-16 animate-fade-in-up">
                    <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4 font-soft">
                        Liên hệ với chúng tôi
                    </h2>
                    <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                        Chúng tôi luôn sẵn sàng hỗ trợ và giải đáp mọi thắc mắc của bạn
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {contactInfo.map((info, index) => (
                        <div key={index} className="card text-center hover-lift animate-fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-primary/10 rounded-full mb-4">
                                <info.icon className="text-red-primary" size={28} />
                            </div>
                            <h3 className="font-bold text-gray-900 mb-2">{info.title}</h3>
                            <p className="text-gray-600">{info.content}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}

// Footer Component
function Footer() {
    return (
        <footer className="bg-gray-900 text-white py-12">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                    <div>
                        <div className="flex items-center space-x-3 mb-4">
                            <div className="w-10 h-10 bg-red-primary rounded-lg flex items-center justify-center">
                                <Building2 className="text-white" size={24} />
                            </div>
                            <h3 className="text-xl font-bold">Phường Đông Mai</h3>
                        </div>
                        <p className="text-gray-400">
                            Hệ thống chuyển đổi số hành chính công. Lấy sự hài lòng của người dân làm mục tiêu phục vụ.
                        </p>
                    </div>

                    <div>
                        <h4 className="font-bold text-lg mb-4">Liên kết nhanh</h4>
                        <ul className="space-y-2">
                            <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Trang chủ</a></li>
                            <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Dịch vụ</a></li>
                            <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Thủ tục</a></li>
                            <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Liên hệ</a></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-bold text-lg mb-4">Kết nối với chúng tôi</h4>
                        <p className="text-gray-400 mb-4">
                            Theo dõi fanpage để cập nhật thông tin mới nhất
                        </p>
                        <button className="bg-red-primary text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors">
                            Theo dõi ngay
                        </button>
                    </div>
                </div>

                <div className="border-t border-gray-800 pt-8 text-center text-gray-400">
                    <p>&copy; 2026 Phường Đông Mai. Bản quyền thuộc về UBND Phường Đông Mai.</p>
                </div>
            </div>
        </footer>
    );
}

// Initialize React App
const root = createRoot(document.getElementById('root'));
root.render(<App />);

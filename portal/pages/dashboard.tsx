import React from 'react';
import styles from '../styles/Main.module.css';

export default function Dashboard() {
  return (
    <div>
      <h1>
        URL Health Checker
      </h1>
      <div className='dashboard'>
        <iframe src="https://prometheus.spinvfx.com:3000/dashboard/snapshot/xS52koHQVkI1lucOOYzmZRWwS30AsXIC" width="430" height="500"></iframe>
        <iframe src="https://prometheus.spinvfx.com:3000/dashboard/snapshot/hZJO6jDfU8Qd6RESUtFuWJ1IeD6khxBC" width="430" height="500"></iframe>
        <iframe src="https://prometheus.spinvfx.com:3000/dashboard/snapshot/SMx6WWCyNDfaBfrI8GM1yciKjZcra8U5" width="430" height="500"></iframe>
      </div>
    </div>
  );
}

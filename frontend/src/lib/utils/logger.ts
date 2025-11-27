/**
 * Simple logging utility for consistent error logging
 */

type LogLevel = 'error' | 'warn' | 'info' | 'debug';

class Logger {
	private isDevelopment = import.meta.env.DEV;

	private log(level: LogLevel, message: unknown, ...args: unknown[]) {
		if (!this.isDevelopment && level === 'debug') {
			return; // Skip debug logs in production
		}

		const timestamp = new Date().toISOString();
		const prefix = `[${timestamp}] [${level.toUpperCase()}]`;

		switch (level) {
			case 'error':
				console.error(prefix, message, ...args);
				break;
			case 'warn':
				console.warn(prefix, message, ...args);
				break;
			case 'info':
				console.info(prefix, message, ...args);
				break;
			case 'debug':
				console.debug(prefix, message, ...args);
				break;
		}
	}

	error(message: unknown, ...args: unknown[]) {
		this.log('error', message, ...args);
	}

	warn(message: unknown, ...args: unknown[]) {
		this.log('warn', message, ...args);
	}

	info(message: unknown, ...args: unknown[]) {
		this.log('info', message, ...args);
	}

	debug(message: unknown, ...args: unknown[]) {
		this.log('debug', message, ...args);
	}
}

export const logger = new Logger();

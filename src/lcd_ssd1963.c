// Commands for sending messages to an ssd1963 lcd driver
//
// Copyright (C) 2018  Kevin O'Connor <kevin@koconnor.net>
//
// This file may be distributed under the terms of the GNU GPLv3 license.

#include "autoconf.h" // CONFIG_CLOCK_FREQ
#include "basecmd.h" // oid_alloc
#include "board/gpio.h" // gpio_out_write
#include "board/irq.h" // irq_poll
#include "board/misc.h" // timer_from_us
#include "board/internal.h" // GPIO
#include "command.h" // DECL_COMMAND
#include "sched.h" // DECL_SHUTDOWN
#include "board/i8080_fsmc.h"

struct i8080 {
    struct gpio_out bl;
    uint32_t cs, rs;
};


/****************************************************************
 * Init functions
 ****************************************************************/


/****************************************************************
 * Transmit functions
 ****************************************************************/

/****************************************************************
 * Interface
 ****************************************************************/

void
command_config_i8080(uint32_t *args)
{
    struct i8080 *s = oid_alloc(args[0], command_config_i8080, sizeof(*s));
    s->bl = gpio_out_setup(GPIO('D', 12), 1);
    s->cs = GPIO('D', 7);
    s->rs = GPIO('E', 2);

    enable_i8080_fsmc(s->cs, s->rs);
}
DECL_COMMAND(command_config_i8080, "config_i8080 oid=%c");


void
command_i8080_read_data(uint32_t *args)
{
    uint16_t dt[8] = {0,0,0,0,0,0,0,0};

    uint8_t cmd = args[1], cnt = args[2];
    i8080_fsmc_rd_multi_data(cmd, &dt[0], cnt);
    sendf("i8080_read_data_out c=%c d1=%c d2=%c d3=%c d4=%c d5=%c d6=%c d7=%c d8=%c", cmd,
	  dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6], dt[7]);
}
DECL_COMMAND(command_i8080_read_data, "i8080_read_data oid=%c cmd=%c cnt=%c");


void
command_i8080_send_cmd(uint32_t *args)
{
    i8080_fsmc_wr_reg(args[1]);
}
DECL_COMMAND(command_i8080_send_cmd, "i8080_send_cmd oid=%c cmd=%c");


void
command_i8080_send_cmd_param(uint32_t *args)
{
    uint16_t count = args[2], *data = command_decode_ptr(args[3]);

    i8080_fsmc_wr_reg(args[1]);

    while (--count) {
	i8080_fsmc_wr_data((*data++));
    }
}
DECL_COMMAND(command_i8080_send_cmd_param, "i8080_send_cmd_param oid=%c cmd=%c param=%*s");


void
command_i8080_fill(uint32_t *args)
{
    uint32_t index=0;
    uint16_t fact = args[1];

    uint16_t sx = fact;
    uint16_t sy = fact;
    uint16_t ex = fact*2;
    uint16_t ey = fact*2;

    /* LCD_WR_REG(0x2A); */
    /* LCD_WR_DATA(sx>>8);LCD_WR_DATA(sx&0xFF); */
    /* LCD_WR_DATA(ex>>8);LCD_WR_DATA(ex&0xFF); */
    /* LCD_WR_REG(0x2B); */
    /* LCD_WR_DATA(sy>>8);LCD_WR_DATA(sy&0xFF); */
    /* LCD_WR_DATA(ey>>8);LCD_WR_DATA(ey&0xFF); */
    /* LCD_WR_REG(0x2C);  // Ready to write memory */
    
    i8080_fsmc_wr_reg(0x2A);
    i8080_fsmc_wr_data(sx>>8);i8080_fsmc_wr_data(sx&0xFF);
    i8080_fsmc_wr_data(ex>>8);i8080_fsmc_wr_data(ex&0xFF);
    i8080_fsmc_wr_reg(0x2B);
    i8080_fsmc_wr_data(sy>>8);i8080_fsmc_wr_data(sy&0xFF);
    i8080_fsmc_wr_data(ey>>8);i8080_fsmc_wr_data(ey&0xFF);
    i8080_fsmc_wr_reg(0x2C);  // Ready to write memory

    for (index=0; index<fact*fact; index++) {
	//	LCD_WR_DATA(0x00DF);
	//	LCD_WR_DATA(fact);
	//	LCD_WR_DATA(0x0760);
	i8080_fsmc_wr_data(0x0760);
    }
      
    sendf("i8080_fill_done");
}
DECL_COMMAND(command_i8080_fill, "i8080_fill oid=%c fact=%c");


void
i8080_shutdown(void)
{
    uint8_t i;
    struct i8080 *s;
    foreach_oid(i, s, command_config_i8080) {
        s->cs = s->rs = 0;
    }
}
DECL_SHUTDOWN(i8080_shutdown);
